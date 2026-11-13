#!/usr/bin/env python3
"""Install the AI Vision All-in-One preview on a local Linux x86-64 Docker host."""

import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
from tempfile import TemporaryDirectory
import time


REPO = "ob-labs/ai-vision-skills"
PLATFORM = "linux/amd64"
PROFILE = "all-in-one-preview"
TAG = re.compile(r"all-in-one-preview-v\d+\.\d+\.\d+-daily\.\d{8}(?:\.\d+)?")
BASE = re.compile(r"delivery-v\d+\.\d+\.\d+-daily\.\d{8}(?:\.\d+)?")
MANIFEST = "all-in-one-manifest.json"
ARCHIVE = "aiv-all-in-one-linux-amd64.tar.gz"
RELEASE_FILES = {MANIFEST, ARCHIVE, "install-all-in-one.py", "SHA256SUMS"}
OWNER = "io.aivision.all-in-one.instance"
RELEASE = "io.aivision.all-in-one.release"


def output(*args):
    return subprocess.check_output(args, text=True).strip()


def resolve_release(tag):
    pages = json.loads(output(
        "gh", "api", "--hostname", "github.com", "--paginate", "--slurp",
        f"repos/{REPO}/releases?per_page=100",
    ))
    releases = [
        release for page in pages for release in page
        if TAG.fullmatch(release["tag_name"]) and (tag is None or tag == release["tag_name"])
        and release["prerelease"] and not release["draft"] and release["published_at"]
        and RELEASE_FILES <= {asset["name"] for asset in release["assets"] if asset["state"] == "uploaded"}
    ]
    if not releases:
        raise ValueError("No published Linux x86-64 All-in-One preview matches the request.")
    return max(releases, key=lambda release: (release["published_at"], release["id"]))["tag_name"]


def verify_package(folder, selected):
    manifest = json.loads((folder / MANIFEST).read_text(encoding="utf-8"))
    if (
        manifest.get("schema_version") != 1
        or manifest.get("profile") != PROFILE
        or manifest.get("platform") != PLATFORM
        or not TAG.fullmatch(manifest["release_tag"])
        or (selected is not None and manifest["release_tag"] != selected)
        or not BASE.fullmatch(manifest["base_release"])
        or manifest.get("archive") != ARCHIVE
        or not re.fullmatch(r"[a-f0-9]{64}", manifest["archive_sha256"])
        or not re.fullmatch(r"sha256:[a-f0-9]{64}", manifest["image_id"])
        or not re.fullmatch(r"aiv-all-in-one:[a-z0-9][a-z0-9._-]*", manifest["image_tag"])
    ):
        raise ValueError("The manifest does not describe the selected All-in-One preview.")

    archive = folder / ARCHIVE
    if archive.stat().st_size != manifest["archive_bytes"]:
        raise ValueError("The image archive size does not match the manifest.")
    digest = hashlib.sha256()
    with archive.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != manifest["archive_sha256"]:
        raise ValueError("The image archive SHA-256 does not match the manifest.")
    return manifest


def verify_resource(kind, resource, labels):
    if resource not in output("docker", kind, "ls", "--format", "{{.Name}}").splitlines():
        return False
    actual = json.loads(output("docker", kind, "inspect", "--format", "{{json .Labels}}", resource)) or {}
    if actual.get(OWNER) != labels[OWNER]:
        raise ValueError(f"Docker {kind} {resource} is already owned by another deployment.")
    if kind == "volume" and actual.get(RELEASE) != labels[RELEASE]:
        raise ValueError(f"Docker volume {resource} belongs to a different preview. "
                         "Use its original release tag or select a new instance name.")
    return True


def prepare_resource(kind, resource, labels):
    if not verify_resource(kind, resource, labels):
        command = ["docker", kind, "create"]
        for label, value in labels.items():
            command.extend(("--label", f"{label}={value}"))
        subprocess.run([*command, resource], check=True)
        verify_resource(kind, resource, labels)


def install(args, folder, manifest):
    name = args.name
    network, volume = name + "-network", name + "-data"
    if output("docker", "info", "--format", "{{.OSType}}/{{.Architecture}}") not in (
        "linux/x86_64", PLATFORM,
    ):
        raise ValueError("A Linux x86-64 Docker daemon is required.")
    if name in output("docker", "container", "ls", "--all", "--format", "{{.Names}}").splitlines():
        raise ValueError(f"Container {name} already exists. Follow the same-version recreation steps to reuse its data.")
    network_labels = {OWNER: name}
    volume_labels = {OWNER: name, RELEASE: manifest["release_tag"]}
    verify_resource("network", network, network_labels)
    verify_resource("volume", volume, volume_labels)

    image = manifest["image_id"]
    image_tag = manifest["image_tag"]
    image_ref = "{{.Id}} {{.Os}}/{{.Architecture}}"
    known_tags = output("docker", "image", "ls", "--format", "{{.Repository}}:{{.Tag}}").splitlines()
    if image_tag in known_tags and output("docker", "image", "inspect", "--format", image_ref, image_tag) != f"{image} {PLATFORM}":
        raise ValueError(f"Docker image tag {image_tag} already points to different bytes.")
    subprocess.run(["docker", "load", "--input", str(folder / ARCHIVE)], check=True)
    if output("docker", "image", "inspect", "--format", image_ref, image_tag) != f"{image} {PLATFORM}":
        raise ValueError("The loaded Docker image does not match the manifest identity and platform.")

    prepare_resource("network", network, network_labels)
    prepare_resource("volume", volume, volume_labels)
    web = f"http://127.0.0.1:{args.web_port}"
    otlp = f"http://127.0.0.1:{args.otlp_port}"
    container = output(
        "docker", "run", "-d", "--name", name, "--platform", PLATFORM, "--pull", "never",
        "--label", f"{OWNER}={name}", "--network", network,
        "--cpus", "2", "--memory", "6g", "--ulimit", "nofile=65536:65536",
        "--ulimit", "core=0", "--stop-timeout", "120",
        "--mount", f"type=volume,source={volume},target=/data",
        "--publish", f"127.0.0.1:{args.web_port}:5174",
        "--publish", f"127.0.0.1:{args.otlp_port}:4318",
        "--env", f"AIVISION_PUBLIC_BASE_URL={web}",
        "--env", f"AIVISION_OTLP_INGEST_ENDPOINT={otlp}", image,
    )
    deadline = time.monotonic() + args.timeout
    print(f"Waiting for {name} to become healthy...", flush=True)
    while time.monotonic() < deadline:
        state = json.loads(output("docker", "inspect", "--format", "{{json .State}}", container))
        if not state["Running"]:
            break
        if state.get("Health", {}).get("Status") == "healthy":
            print(f"AI Vision is ready at {web}. OTLP HTTP: {otlp}.")
            print(f"Preview: {manifest['release_tag']}. Matching CLI release: {manifest['base_release']}.")
            print(f"Image: {image}. Persistent Docker volume: {volume}.")
            return
        time.sleep(3)
    raise ValueError(f"{name} did not become ready. Inspect with docker logs {name}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--tag", help="Pin an exact published All-in-One preview tag.")
    source.add_argument("--from-dir", type=Path, help="Install from a trusted local release asset directory.")
    source.add_argument("--resolve", action="store_true", help="Print the latest compatible published preview tag.")
    parser.add_argument("--name", default="aiv-all-in-one", help="Docker resource name prefix.")
    parser.add_argument("--web-port", type=int, default=5174)
    parser.add_argument("--otlp-port", type=int, default=4318)
    parser.add_argument("--timeout", type=int, default=300, help="Readiness timeout in seconds.")
    args = parser.parse_args()

    try:
        if platform.system() != "Linux" or platform.machine() not in ("x86_64", "amd64"):
            raise ValueError("All-in-One is currently available on Linux x86-64.")
        if args.tag is not None and not TAG.fullmatch(args.tag):
            raise ValueError("Specify an exact All-in-One preview tag.")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,47}", args.name):
            raise ValueError("Use a name of 2–48 lowercase letters, digits or hyphens, starting with a letter or digit.")
        ports = {args.web_port, args.otlp_port}
        if len(ports) != 2 or min(ports) < 1 or max(ports) > 65535 or args.timeout < 1:
            raise ValueError("Specify distinct TCP ports in 1–65535 and a positive readiness timeout.")

        tag = None if args.from_dir else resolve_release(args.tag)
        if args.resolve:
            print(tag)
            return 0
        with (nullcontext(args.from_dir) if args.from_dir else TemporaryDirectory(prefix="aiv-all-in-one-")) as directory:
            folder = Path(directory).resolve()
            if tag:
                print(f"Downloading {tag}...", flush=True)
                subprocess.run(["gh", "release", "download", tag, "--repo", f"github.com/{REPO}",
                                "--dir", str(folder), "--pattern", MANIFEST, "--pattern", ARCHIVE], check=True)
            manifest = verify_package(folder, tag)
            install(args, folder, manifest)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"All-in-One installation failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
