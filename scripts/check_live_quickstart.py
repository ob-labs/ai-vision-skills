#!/usr/bin/env python3
"""Install the latest published Personal Edition Daily and run browser Quickstart."""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import re
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from uuid import uuid4


REPO = "antgroup/ai-vision"
DAILY = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+-daily\.[0-9]{8}(\.[0-9]+)?")
HOSTS = {"api.github.com", "github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"}
MANIFEST, SUMS, INSTALLER = "release-manifest.json", "SHA256SUMS", "install-all-in-one.py"
PLATFORMS = {
    "amd64": ("all-in-one-manifest.json", "aiv-all-in-one-linux-amd64.tar.gz", "aiv-linux-x64.tar.gz"),
    "arm64": ("all-in-one-manifest-arm64.json", "aiv-all-in-one-linux-arm64.tar.gz", "aiv-linux-arm64.tar.gz"),
}
ARCHITECTURES = {"amd64": "amd64", "x86_64": "amd64", "arm64": "arm64", "aarch64": "arm64"}
OWNER = "io.aivision.all-in-one.instance"
RELEASE = "io.aivision.all-in-one.release"
BROWSER = Path(__file__).with_name("live_quickstart_browser.cjs").resolve()


class SafeRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        origin = urlsplit(req.full_url)
        target = urlsplit(newurl)
        if origin.scheme == "https":
            allowed = target.scheme == "https" and target.netloc in HOSTS
        else:
            allowed = target.scheme == "http" and target.netloc == origin.netloc
        if not allowed:
            raise ValueError("Unexpected redirect during the public download or loopback check")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


HTTP = build_opener(ProxyHandler({}), SafeRedirects())


def download(url):
    request = Request(url, headers={"User-Agent": "ai-vision-skills-live-quickstart"})
    with HTTP.open(request, timeout=30) as response:
        limit = 16 * 1024 * 1024  # Release metadata, not Docker archives.
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Official Release metadata exceeded the download limit")
    return data


def release_asset(tag, assets, name):
    data = download(f"https://github.com/{REPO}/releases/download/{tag}/{name}")
    metadata = assets[name]
    digest = metadata.get("digest")
    if len(data) != metadata["size"] or (digest and digest != f"sha256:{sha256(data).hexdigest()}"):
        raise ValueError(f"{tag} {name} does not match GitHub Release metadata")
    return data


def latest_personal_daily():
    # Sort by publication time like the official installer. GitHub's releases
    # endpoint lists releases by creation time, which can differ after staging.
    candidates = []
    for page in range(1, 11):
        releases = json.loads(download(f"https://api.github.com/repos/{REPO}/releases?per_page=100&page={page}"))
        if not isinstance(releases, list):
            raise ValueError("GitHub did not return a release list")
        candidates.extend(release for release in releases if (
            not release["draft"] and release["prerelease"] and release["published_at"]
            and DAILY.fullmatch(release["tag_name"])
        ))
        if len(releases) < 100:
            break
    else:
        raise ValueError("GitHub Release listing exceeded the supported page limit")

    for release in sorted(candidates, key=lambda item: (item["published_at"], item["id"]), reverse=True):
        tag = release["tag_name"]
        assets = {asset["name"]: asset for asset in release["assets"] if asset["state"] == "uploaded"}
        if MANIFEST not in assets:
            raise ValueError(f"Published Daily {tag} has no {MANIFEST}; cannot determine its edition")
        manifest_bytes = release_asset(tag, assets, MANIFEST)
        manifest = json.loads(manifest_bytes)
        if manifest.get("personal_edition") is not True:
            continue
        if (manifest.get("release_tag"), manifest.get("source_repository")) != (tag, REPO):
            raise ValueError(f"Personal Edition manifest identity does not match {tag}")

        required = {INSTALLER, SUMS, *(name for bundle in PLATFORMS.values() for name in bundle)}
        missing = required - assets.keys()
        if missing:
            raise ValueError(f"Newest Personal Edition Daily {tag} is incomplete: {', '.join(sorted(missing))}")
        return tag, assets, manifest_bytes
    raise ValueError("No published versioned Personal Edition Daily was found")


def check_asset_checksum(data, name, sums):
    entries = [entry[0] for line in sums.splitlines() if len(entry := line.split()) == 2 and entry[1] == name]
    if entries != [sha256(data).hexdigest()]:
        raise ValueError(f"{name} does not match the official SHA256SUMS")


def stage_installer(directory, architecture):
    tag, assets, product = latest_personal_daily()
    sums = release_asset(tag, assets, SUMS).decode("ascii")
    check_asset_checksum(product, MANIFEST, sums)
    installer = release_asset(tag, assets, INSTALLER)
    check_asset_checksum(installer, INSTALLER, sums)
    manifest_name = PLATFORMS[architecture][0]
    manifest_bytes = release_asset(tag, assets, manifest_name)
    check_asset_checksum(manifest_bytes, manifest_name, sums)
    manifest = json.loads(manifest_bytes)
    if (manifest.get("release_tag"), manifest.get("platform")) != (tag, f"linux/{architecture}"):
        raise ValueError(f"{manifest_name} does not describe {tag} for linux/{architecture}")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", manifest.get("image_id", "")):
        raise ValueError(f"{manifest_name} does not identify the published Docker image")
    (directory / INSTALLER).write_bytes(installer)
    return tag, manifest


def clean_environment(home):
    host = os.environ.get("DOCKER_HOST") or "unix:///var/run/docker.sock"
    endpoint = urlsplit(host)
    if endpoint.scheme != "unix" or endpoint.netloc or not endpoint.path.startswith("/"):
        raise ValueError("Live Quickstart requires a local Unix-socket Docker daemon")
    home.mkdir()
    return {
        **{key: os.environ[key] for key in ("PATH", "NODE_PATH", "PLAYWRIGHT_BROWSERS_PATH")
           if key in os.environ},
        "HOME": str(home),
        "TMPDIR": str(home),
        "DOCKER_HOST": host,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
    }


def docker(env, *arguments, timeout=30):
    return subprocess.check_output(["docker", *arguments], text=True, env=env, timeout=timeout).strip()


def free_ports():
    with socket.socket() as web, socket.socket() as otlp:
        web.bind(("127.0.0.1", 0))
        otlp.bind(("127.0.0.1", 0))
        return web.getsockname()[1], otlp.getsockname()[1]


def resources(name):
    return (("container", name), ("network", name + "-network"), ("volume", name + "-data"))


def exists(env, kind, name):
    flags = ("--all", "--format", "{{.Names}}") if kind == "container" else ("--format", "{{.Name}}")
    return name in docker(env, kind, "ls", *flags).splitlines()


def inspect(env, kind, name):
    return json.loads(docker(env, kind, "inspect", name))[0]


def cleanup(env, name, tag):
    failures = []
    for kind, resource in resources(name):
        try:
            if not exists(env, kind, resource):
                continue
            details = inspect(env, kind, resource)
            labels = details["Config"].get("Labels") if kind == "container" else details.get("Labels")
            if not labels or labels.get(OWNER) != name or (kind == "volume" and labels.get(RELEASE) != tag):
                raise ValueError("resource does not have the expected All-in-One ownership labels")
            if kind == "container":
                docker(env, kind, "rm", "--force", details["Id"])
            else:
                docker(env, kind, "rm", details["Id"] if kind == "network" else resource)
        except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
            failures.append(f"{kind} {resource}: {error}")
    if not failures:
        print("Scoped Quickstart container, network, and volume cleaned up.", flush=True)
        return
    message = "Unable to clean up the scoped Quickstart resources: " + "; ".join(failures)
    if sys.exc_info()[0] is None:
        raise RuntimeError(message)
    print(message, file=sys.stderr)


def verify_running_install(env, name, tag, manifest, web_port, otlp_port):
    container = inspect(env, "container", name)
    volume = name + "-data"
    if (container["Image"] != manifest["image_id"] or not container["State"]["Running"]
            or container["State"].get("Health", {}).get("Status") != "healthy"
            or container["Config"]["Labels"].get(OWNER) != name
            or not any(mount.get("Name") == volume and mount.get("Destination") == "/data"
                       for mount in container["Mounts"])
            or inspect(env, "volume", volume)["Labels"].get(RELEASE) != tag):
        raise ValueError(f"{name} is not a healthy, volume-backed instance of {tag}")
    published = container["NetworkSettings"]["Ports"]
    for key, port in (("5174/tcp", web_port), ("4318/tcp", otlp_port)):
        if published.get(key) != [{"HostIp": "127.0.0.1", "HostPort": str(port)}]:
            raise ValueError(f"{name} did not bind {key} to the expected loopback port")
    origin = f"http://127.0.0.1:{web_port}"
    with HTTP.open(origin, timeout=15) as response:
        if response.status != 200:
            raise ValueError("All-in-One web endpoint did not return HTTP 200")
    print(f"Verified healthy All-in-One {tag} ({manifest['platform']}, {manifest['image_id']}).", flush=True)
    return origin


def smoke(work, cache):
    architecture = ARCHITECTURES.get(platform.machine().lower())
    if platform.system() != "Linux" or architecture is None:
        raise ValueError("Live Quickstart requires Linux amd64 or ARM64")
    env = clean_environment(work / "home")
    server = docker(env, "info", "--format", "{{.OSType}}/{{.Architecture}}")
    os_type, _, server_architecture = server.partition("/")
    if os_type != "linux" or ARCHITECTURES.get(server_architecture) != architecture:
        raise ValueError("Linux host and local Docker architecture do not match")
    tag, manifest = stage_installer(work, architecture)
    major = docker(env, "version", "--format", "{{.Server.Version}}").split(".", 1)[0]
    archive_format = "zstd" if int(major) >= 23 and manifest.get("zstd_archive") else "gzip"
    print(f"Resolved latest published Personal Edition Daily {tag}; installing {archive_format} on linux/{architecture}.", flush=True)

    name = "aiv-live-quickstart-" + uuid4().hex[:16]
    web, otlp = free_ports()
    if any(exists(env, kind, resource) for kind, resource in resources(name)):
        raise ValueError("Refusing to reuse a Docker resource for Live Quickstart")
    try:
        subprocess.run([
            sys.executable, "-IB", str(work / INSTALLER), "--tag", tag,
            "--name", name, "--web-port", str(web), "--otlp-port", str(otlp),
            "--archive-format", archive_format, "--cache-dir", str(cache or work / "cache"),
        ], check=True, env=env, cwd=work, timeout=600)
        origin = verify_running_install(env, name, tag, manifest, web, otlp)
        subprocess.run(["node", str(BROWSER), origin], check=True, env=env, cwd=work, timeout=240)
    finally:
        cleanup(env, name, tag)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, help="Reuse an image archive verified by the official installer")
    args = parser.parse_args()
    try:
        with TemporaryDirectory(prefix="aiv-live-quickstart-") as directory:
            smoke(Path(directory).resolve(), args.cache_dir.expanduser().resolve() if args.cache_dir else None)
    except (ValueError, RuntimeError, KeyError, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Live Quickstart failed: {error}\n")


if __name__ == "__main__":
    main()
