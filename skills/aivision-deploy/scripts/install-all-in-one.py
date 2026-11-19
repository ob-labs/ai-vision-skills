#!/usr/bin/env python3
"""Install AI Vision All-in-One Personal Edition on a supported local Linux Docker host."""

import argparse
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import socket
import subprocess
import sys
import tarfile
from tempfile import NamedTemporaryFile, TemporaryDirectory
import time


REPO = "antgroup/ai-vision"
PRODUCT_PROFILE = "all-in-one"
LEGACY_PROFILE = "all-in-one-preview"
DAILY_VERSION = r"\d+\.\d+\.\d+-daily\.\d{8}(?:\.\d+)?"
PRODUCT_TAG = re.compile(rf"v{DAILY_VERSION}")
TAG = re.compile(rf"(?:all-in-one-preview-)?{PRODUCT_TAG.pattern}")
# Existing offline bundles may still carry the former delivery- tag prefix.
BASE = re.compile(rf"(?:delivery-)?v({DAILY_VERSION})")
ARCHITECTURES = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}
ASSETS = {
    "linux/amd64": ("all-in-one-manifest.json", "aiv-all-in-one-linux-amd64.tar.gz", "aiv-linux-x64.tar.gz"),
    "linux/arm64": (
        "all-in-one-manifest-arm64.json", "aiv-all-in-one-linux-arm64.tar.gz", "aiv-linux-arm64.tar.gz",
    ),
}
ELF_MACHINES = {"linux/amd64": 62, "linux/arm64": 183}
SHA256 = re.compile(r"[a-f0-9]{64}")
SUMS = "SHA256SUMS"
PRODUCT_MANIFEST = "release-manifest.json"
SOURCE_KEYS = ("source_repository", "release_tag", "source_sha", "build_id")
SAMPLE = "sample-trace.py"
OWNER = "io.aivision.all-in-one.instance"
RELEASE = "io.aivision.all-in-one.release"


def output(*args):
    return subprocess.check_output(args, text=True).strip()


def linux_platform(system, architecture):
    if system.lower() != "linux" or architecture not in ARCHITECTURES:
        raise ValueError("All-in-One requires Linux x86-64 or ARM64.")
    return f"linux/{ARCHITECTURES[architecture]}"


def resolve_release(tag, target):
    manifest, image, cli = ASSETS[target]
    required_assets = {manifest, image, "install-all-in-one.py", SUMS}
    if target == "linux/arm64":
        required_assets.add(cli)
    product_assets = required_assets | {cli, PRODUCT_MANIFEST}
    pages = json.loads(output(
        "gh", "api", "--hostname", "github.com", "--paginate", "--slurp",
        f"repos/{REPO}/releases?per_page=100",
    ))
    releases = [
        release for page in pages for release in page
        if TAG.fullmatch(release["tag_name"]) and (tag is None or tag == release["tag_name"])
        and release["prerelease"] and not release["draft"] and release["published_at"]
        and (product_assets if PRODUCT_TAG.fullmatch(release["tag_name"]) else required_assets)
        <= {asset["name"] for asset in release["assets"] if asset["state"] == "uploaded"}
    ]
    if not releases:
        raise ValueError(f"No published All-in-One release for {target} matches the request in {REPO}.")
    return max(releases, key=lambda release: (release["published_at"], release["id"]))["tag_name"]


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(path, sha256, size=None):
    if size is not None and path.stat().st_size != size:
        raise ValueError(f"{path.name} size does not match the expected bytes.")
    if file_sha256(path) != sha256:
        raise ValueError(f"{path.name} SHA-256 does not match the expected digest.")


def published_assets(tag):
    release = json.loads(output("gh", "api", "--hostname", "github.com", f"repos/{REPO}/releases/tags/{tag}"))
    if (release["tag_name"] != tag or release["draft"] or not release["prerelease"]
            or not release["published_at"]):
        raise ValueError(f"{tag} is not an exact published prerelease.")
    return {asset["name"]: asset for asset in release["assets"] if asset["state"] == "uploaded"}


def asset_identity(assets, name):
    asset = assets.get(name, {})
    algorithm, _, digest = (asset.get("digest") or "").partition(":")
    size = asset.get("size")
    if algorithm != "sha256" or not SHA256.fullmatch(digest) or not require_size(size):
        raise ValueError(f"Missing authenticated GitHub digest or size for {name}.")
    return digest, size


def download(folder, tag, *names):
    command = ["gh", "release", "download", tag, "--repo", f"github.com/{REPO}", "--dir", str(folder)]
    for name in names:
        command.extend(("--pattern", name))
    subprocess.run(command, check=True)


def sum_for(folder, name):
    matches = [entry[0] for line in (folder / SUMS).read_text(encoding="ascii").splitlines()
               if len(entry := line.split()) == 2 and entry[1] == name and SHA256.fullmatch(entry[0])]
    if len(matches) != 1:
        raise ValueError(f"Expected one checksum for {name} in {SUMS}.")
    return matches[0]


def require_size(value):
    return type(value) is int and value > 0


def read_manifest(folder, selected, target):
    manifest_name, archive, client_archive = ASSETS[target]
    manifest = json.loads((folder / manifest_name).read_text(encoding="utf-8"))
    base = BASE.fullmatch(manifest["base_release"])
    tag = manifest["release_tag"]
    product = PRODUCT_TAG.fullmatch(tag) is not None
    if (
        manifest.get("schema_version") != 1
        or manifest.get("profile") != (PRODUCT_PROFILE if product else LEGACY_PROFILE)
        or manifest.get("platform") != target
        or not TAG.fullmatch(tag)
        or (selected is not None and tag != selected)
        or base is None
        or (product and manifest["base_release"] != tag)
        or manifest.get("archive") != archive
        or not SHA256.fullmatch(manifest["archive_sha256"])
        or not require_size(manifest.get("archive_bytes"))
        or not re.fullmatch(r"sha256:[a-f0-9]{64}", manifest["image_id"])
        or not re.fullmatch(r"aiv-all-in-one:[a-z0-9][a-z0-9._-]*", manifest["image_tag"])
    ):
        raise ValueError("The manifest does not describe the selected All-in-One release.")

    zstd_fields = {"zstd_archive", "zstd_archive_bytes", "zstd_archive_sha256"}
    if zstd_fields.intersection(manifest) and (
        manifest.get("zstd_archive") != archive[:-2] + "zst"
        or not require_size(manifest.get("zstd_archive_bytes"))
        or not SHA256.fullmatch(manifest.get("zstd_archive_sha256", ""))
    ):
        raise ValueError("The manifest has an invalid zstd image archive.")

    if product or target == "linux/arm64" or "agent_cli" in manifest:
        client = manifest.get("agent_cli")
        if (
            not isinstance(client, dict)
            or client.get("archive") != client_archive
            or client.get("version") != base.group(1)
            or not SHA256.fullmatch(client.get("archive_sha256", ""))
            or not SHA256.fullmatch(client.get("binary_sha256", ""))
            or not require_size(client.get("archive_bytes"))
        ):
            raise ValueError("The All-in-One manifest is missing a matching Agent CLI.")
    return manifest


def verify_client_archive(folder, manifest):
    if "agent_cli" in manifest:
        client = manifest["agent_cli"]
        verify_file(folder / client["archive"], client["archive_sha256"], client["archive_bytes"])


def image_archive(folder, manifest, assets, requested, zstd_supported):
    zstd_name = manifest.get("zstd_archive")
    zstd_available = bool(zstd_name) and (zstd_name in assets if assets is not None else (folder / zstd_name).is_file())
    if requested == "zstd" and not zstd_supported:
        raise ValueError("This Docker server version is outside the zstd support threshold. Use gzip.")
    if requested == "zstd" and not zstd_available:
        raise ValueError("This release has no zstd archive available for the selected architecture.")
    prefix = "zstd_" if requested != "gzip" and zstd_supported and zstd_available else ""
    name, digest, size = (manifest[prefix + field] for field in ("archive", "archive_sha256", "archive_bytes"))
    if assets is not None:
        verify_asset_metadata(assets, name, digest, size)
    else:
        if sum_for(folder, name) != digest:
            raise ValueError(f"The checksum for {name} differs from the manifest.")
        verify_file(folder / name, digest, size)
    return name, digest, size


def cached_image_archive(cache_dir, tag, name, digest, size):
    directory = cache_dir.expanduser() / digest
    archive = directory / name
    if archive.is_file():
        try:
            verify_file(archive, digest, size)
        except ValueError:
            print(f"Cached {name} failed verification; downloading a fresh copy.", flush=True)
        else:
            print(f"Using verified cached archive {name}.", flush=True)
            return archive
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    print(f"Downloading {tag}: {name} ({size} bytes)...", flush=True)
    with TemporaryDirectory(dir=directory) as staging:
        folder = Path(staging)
        download(folder, tag, name)
        verify_file(folder / name, digest, size)
        (folder / name).replace(archive)
    return archive


def verify_product_manifest(folder, manifest):
    path = folder / PRODUCT_MANIFEST
    verify_file(path, sum_for(folder, PRODUCT_MANIFEST))
    product = json.loads(path.read_text(encoding="utf-8"))
    source = {key: product.get(key) for key in SOURCE_KEYS}
    tag = manifest["release_tag"]
    if (
        source != manifest.get("source_candidate")
        or source["source_repository"] != REPO
        or source["release_tag"] != tag
        or product.get("product_version") != tag[1:]
        or product.get("channel") != "daily"
        or product.get("personal_edition") is not True
        or not re.fullmatch(r"[0-9a-f]{40}", source["source_sha"] or "")
        or not re.fullmatch(r"[1-9][0-9]*\.[1-9][0-9]*", source["build_id"] or "")
    ):
        raise ValueError("The All-in-One source candidate differs from the product Release manifest.")

    cli = manifest["agent_cli"]
    checksums = {manifest["archive"]: manifest["archive_sha256"], cli["archive"]: cli["archive_sha256"]}
    if "zstd_archive" in manifest:
        checksums[manifest["zstd_archive"]] = manifest["zstd_archive_sha256"]
    for name, digest in checksums.items():
        if sum_for(folder, name) != digest:
            raise ValueError(f"The checksum for {name} differs from the manifest.")


def release_manifest(folder, tag, target):
    name = ASSETS[target][0]
    assets = {}
    if tag is not None:
        assets = published_assets(tag)
        names = (SUMS, PRODUCT_MANIFEST, name) if PRODUCT_TAG.fullmatch(tag) else (name,)
        identities = {filename: asset_identity(assets, filename) for filename in names}
        download(folder, tag, *names)
        for filename, identity in identities.items():
            verify_file(folder / filename, *identity)
    if tag is None or PRODUCT_TAG.fullmatch(tag):
        verify_file(folder / name, sum_for(folder, name))
    manifest = read_manifest(folder, tag, target)
    if manifest["profile"] == PRODUCT_PROFILE:
        verify_product_manifest(folder, manifest)
    return manifest, assets


def verify_asset_metadata(assets, name, digest, size):
    if asset_identity(assets, name) != (digest, size):
        raise ValueError(f"Authenticated GitHub identity for {name} differs from the manifest.")


def select_cli(folder, manifest, target, assets, online):
    bundle_tag = manifest["release_tag"]
    client = manifest.get("agent_cli")
    if client is not None:
        if online:
            verify_asset_metadata(assets, client["archive"], client["archive_sha256"], client["archive_bytes"])
        release_tag = bundle_tag
    else:
        if not online:
            raise ValueError("This legacy x86-64 bundle uses a separate CLI release. Use --tag for CLI access.")
        release_tag = manifest["base_release"]
        cli_assets = published_assets(release_tag)
        archive = ASSETS[target][2]
        digest, size = asset_identity(cli_assets, archive)
        download(folder, release_tag, SUMS)
        verify_file(folder / SUMS, *asset_identity(cli_assets, SUMS))
        if sum_for(folder, archive) != digest:
            raise ValueError("The base CLI archive checksum differs from authenticated GitHub metadata.")
        client = {"archive": archive, "archive_sha256": digest, "archive_bytes": size,
                  "version": BASE.fullmatch(release_tag).group(1)}
    return {**client, "platform": target, "preview_tag": bundle_tag, "release_tag": release_tag,
            "repository": REPO}


def verify_cli_platform(path, target):
    with path.open("rb") as executable:
        header = executable.read(20)
    if header[:7] != b"\x7fELF\x02\x01\x01" or int.from_bytes(header[18:20], "little") != ELF_MACHINES[target]:
        raise ValueError(f"The CLI executable does not match {target}.")


def install_cli(folder, selection, install_dir, online):
    archive = selection["archive"]
    if online:
        download(folder, selection["release_tag"], archive)
    else:
        if sum_for(folder, archive) != selection["archive_sha256"]:
            raise ValueError(f"The checksum for {archive} differs from the manifest.")
    verify_file(folder / archive, selection["archive_sha256"], selection["archive_bytes"])
    install_dir = install_dir.expanduser().resolve()
    install_dir.mkdir(parents=True, exist_ok=True)
    destination = install_dir / "aiv"
    with NamedTemporaryFile(prefix=".aiv-install.", dir=install_dir, delete=False) as staged:
        staged_path = Path(staged.name)
    try:
        with tarfile.open(folder / archive, "r:gz") as bundle:
            entries = [member for member in bundle.getmembers() if member.name == "aiv"]
            if len(entries) != 1 or not entries[0].isfile():
                raise ValueError("The CLI archive must contain exactly one regular file named aiv.")
            with bundle.extractfile(entries[0]) as source, staged_path.open("wb") as destination_file:
                shutil.copyfileobj(source, destination_file)
        if "binary_sha256" in selection:
            verify_file(staged_path, selection["binary_sha256"])
        verify_cli_platform(staged_path, selection["platform"])
        staged_path.chmod(0o755)
        if output(str(staged_path), "--version") != f"aiv {selection['version']}":
            raise ValueError("The aiv executable version differs from the selected release.")
        staged_path.replace(destination)
    finally:
        staged_path.unlink(missing_ok=True)
    print(f"Installed {destination} ({selection['platform']}, aiv {selection['version']}).")


def verify_resource(kind, resource, labels):
    if resource not in output("docker", kind, "ls", "--format", "{{.Name}}").splitlines():
        return False
    actual = json.loads(output("docker", kind, "inspect", "--format", "{{json .Labels}}", resource)) or {}
    if actual.get(OWNER) != labels[OWNER]:
        raise ValueError(f"Docker {kind} {resource} is already owned by another deployment.")
    if kind == "volume" and actual.get(RELEASE) != labels[RELEASE]:
        raise ValueError(f"Docker volume {resource} belongs to a different All-in-One release. "
                         "Use its original release tag or select a new instance name.")
    return True


def prepare_resource(kind, resource, labels):
    if not verify_resource(kind, resource, labels):
        command = ["docker", kind, "create"]
        for label, value in labels.items():
            command.extend(("--label", f"{label}={value}"))
        subprocess.run([*command, resource], check=True)
        verify_resource(kind, resource, labels)


def preflight(args, target):
    info = output("docker", "info", "--format", "{{.OSType}}/{{.Architecture}}")
    docker_system, _, docker_architecture = info.partition("/")
    if linux_platform(docker_system, docker_architecture) != target:
        raise ValueError(f"A matching local {target} Docker daemon is required.")
    if args.name in output("docker", "container", "ls", "--all", "--format", "{{.Names}}").splitlines():
        raise ValueError(f"Container {args.name} already exists. Follow the same-version recreation steps to reuse its data.")
    for port in (args.web_port, args.otlp_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                listener.bind(("127.0.0.1", port))
                listener.listen(1)
            except OSError as error:
                raise ValueError(f"Cannot bind local port {port}: {error}. Choose an available port.") from error
    version = output("docker", "version", "--format", "{{.Server.Version}}")
    major = re.match(r"^(\d+)\.", version)
    return major is not None and int(major[1]) >= 23


def local_image(manifest):
    image_tag = manifest["image_tag"]
    known_tags = output("docker", "image", "ls", "--format", "{{.Repository}}:{{.Tag}}").splitlines()
    if image_tag not in known_tags:
        return False
    image_ref = "{{.Id}} {{.Os}}/{{.Architecture}}"
    if output("docker", "image", "inspect", "--format", image_ref, image_tag) != f"{manifest['image_id']} {manifest['platform']}":
        raise ValueError(f"Docker image tag {image_tag} already points to different bytes.")
    return True


def check_resources(name, manifest):
    network_labels = {OWNER: name}
    volume_labels = {OWNER: name, RELEASE: manifest["release_tag"]}
    verify_resource("network", name + "-network", network_labels)
    verify_resource("volume", name + "-data", volume_labels)
    return network_labels, volume_labels


def install(args, manifest, archive, labels):
    name = args.name
    network, volume = name + "-network", name + "-data"
    network_labels, volume_labels = labels
    target = manifest["platform"]

    image = manifest["image_id"]
    image_tag = manifest["image_tag"]
    image_ref = "{{.Id}} {{.Os}}/{{.Architecture}}"
    if archive is not None:
        print(f"Loading {archive.name} into Docker...", flush=True)
        subprocess.run(["docker", "load", "--input", str(archive)], check=True)
    if output("docker", "image", "inspect", "--format", image_ref, image_tag) != f"{image} {target}":
        raise ValueError("The loaded Docker image does not match the manifest identity and platform.")

    prepare_resource("network", network, network_labels)
    prepare_resource("volume", volume, volume_labels)
    web = f"http://127.0.0.1:{args.web_port}"
    otlp = f"http://127.0.0.1:{args.otlp_port}"
    container = output(
        "docker", "run", "-d", "--name", name, "--platform", target, "--pull", "never",
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
            if "agent_cli" in manifest:
                client = manifest["agent_cli"]
                print(f"All-in-One release: {manifest['release_tag']} ({target}). Base release: {manifest['base_release']}.")
                print(f"Matching Agent CLI: {client['archive']} (aiv {client['version']}) from this release.")
            else:
                print(f"All-in-One release: {manifest['release_tag']}. Matching CLI release: {manifest['base_release']}.")
            print(f"Image: {image}. Persistent Docker volume: {volume}.")
            return
        time.sleep(3)
    raise ValueError(f"{name} did not become ready. Inspect with docker logs {name}. "
                     f"The container and {volume} were retained for troubleshooting.")


def deploy(args, folder, tag, manifest, assets, zstd_supported):
    labels = check_resources(args.name, manifest)
    loaded = local_image(manifest)
    if tag and "agent_cli" in manifest:
        client = manifest["agent_cli"]
        verify_asset_metadata(assets, client["archive"], client["archive_sha256"], client["archive_bytes"])
        download(folder, tag, client["archive"])
    verify_client_archive(folder, manifest)
    archive = None
    if not loaded or args.archive_format != "auto" or tag is None:
        selected = image_archive(folder, manifest, assets if tag else None, args.archive_format, zstd_supported)
        archive = cached_image_archive(args.cache_dir, tag, *selected) if tag else folder / selected[0]
    else:
        print(f"Using verified local image {manifest['image_id']}.", flush=True)
    install(args, manifest, archive, labels)


def sample_instance(name):
    template = '{{json .Config.Labels}}\n{{json .State.Health.Status}}\n{{json .NetworkSettings.Ports}}\n{{json .Mounts}}'
    labels, health, published, mounts = (json.loads(part) for part in output("docker", "inspect", "--format", template, name).splitlines())
    volume = name + "-data"
    if labels.get(OWNER) != name or health != "healthy" or not any(
        mount["Type"] == "volume" and mount["Name"] == volume and mount["Destination"] == "/data" for mount in mounts
    ):
        raise ValueError(f"{name} is not a healthy All-in-One container with its named data volume.")
    volume_labels = json.loads(output("docker", "volume", "inspect", "--format", "{{json .Labels}}", volume))
    tag = volume_labels.get(RELEASE, "")
    if volume_labels.get(OWNER) != name or not TAG.fullmatch(tag):
        raise ValueError(f"Docker volume {volume} does not identify the installed release.")
    ports = []
    for container_port in ("5174/tcp", "4318/tcp"):
        bindings = [int(entry["HostPort"]) for entry in (published.get(container_port) or [])
                    if entry["HostIp"] == "127.0.0.1"]
        if len(bindings) != 1:
            raise ValueError(f"{name} must publish {container_port} on one local IPv4 port.")
        ports.extend(bindings)
    return tag, ports


def sample_trace(args, target):
    tag, (web_port, otlp_port) = sample_instance(args.name)
    if args.tag and args.tag != tag:
        raise ValueError(f"{args.name} uses {tag}. Select that exact release for its sample Trace.")
    with (nullcontext(args.from_dir) if args.from_dir else TemporaryDirectory(prefix="aiv-sample-trace-")) as directory:
        folder = Path(directory).resolve()
        if args.from_dir:
            if release_manifest(folder, None, target)[0]["release_tag"] != tag:
                raise ValueError(f"The local bundle does not match {args.name}'s release {tag}.")
            verify_file(folder / SAMPLE, sum_for(folder, SAMPLE))
        else:
            product = PRODUCT_TAG.fullmatch(tag) is not None
            assets = release_manifest(folder, tag, target)[1] if product else published_assets(tag)
            digest, size = asset_identity(assets, SAMPLE)
            if product and sum_for(folder, SAMPLE) != digest:
                raise ValueError(f"The checksum for {SAMPLE} differs from authenticated GitHub metadata.")
            download(folder, tag, SAMPLE)
            verify_file(folder / SAMPLE, digest, size)
        subprocess.run([sys.executable, str(folder / SAMPLE), "--web-port", str(web_port),
                        "--otlp-port", str(otlp_port)], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--tag", help="Pin an exact published All-in-One release tag.")
    source.add_argument("--from-dir", type=Path, help="Install from a trusted local release asset directory.")
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument("--resolve", action="store_true", help="Print the compatible published release tag.")
    operation.add_argument("--resolve-cli", action="store_true", help="Print the matching Agent CLI selection as JSON.")
    operation.add_argument("--install-cli", action="store_true", help="Install the matching Agent CLI without Docker.")
    operation.add_argument("--sample-trace", action="store_true", help="Send a synthetic Trace to a running local instance.")
    parser.add_argument("--install-dir", type=Path, default=Path("~/.local/bin"), help="Directory for --install-cli.")
    parser.add_argument("--archive-format", choices=("auto", "gzip", "zstd"), default="auto",
                        help="Image archive format. Auto prefers zstd on compatible Docker servers.")
    parser.add_argument("--cache-dir", type=Path, default=Path(os.environ.get("XDG_CACHE_HOME") or "~/.cache") / "aivision/all-in-one",
                        help="Location of verified image downloads.")
    parser.add_argument("--name", default="aiv-all-in-one", help="Docker resource name prefix.")
    parser.add_argument("--web-port", type=int, default=5174)
    parser.add_argument("--otlp-port", type=int, default=4318)
    parser.add_argument("--timeout", type=int, default=300, help="Readiness timeout in seconds.")
    args = parser.parse_args()

    try:
        target = linux_platform(platform.system(), platform.machine())
        if args.tag is not None and not TAG.fullmatch(args.tag):
            raise ValueError("Specify an exact All-in-One release tag.")
        if args.resolve and args.from_dir:
            raise ValueError("--resolve selects a published release. Use --resolve-cli for a local CLI selection.")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,47}", args.name):
            raise ValueError("Use a name of 2–48 lowercase letters, digits or hyphens, starting with a letter or digit.")
        ports = {args.web_port, args.otlp_port}
        if len(ports) != 2 or min(ports) < 1 or max(ports) > 65535 or args.timeout < 1:
            raise ValueError("Specify distinct TCP ports in 1–65535 and a positive readiness timeout.")

        if args.sample_trace:
            sample_trace(args, target)
            return 0
        deploying = not (args.resolve or args.resolve_cli or args.install_cli)
        zstd_supported = preflight(args, target) if deploying else False
        tag = None if args.from_dir else resolve_release(args.tag, target)
        if args.resolve:
            print(tag)
            return 0
        with (nullcontext(args.from_dir) if args.from_dir else TemporaryDirectory(prefix="aiv-all-in-one-")) as directory:
            folder = Path(directory).resolve()
            manifest, assets = release_manifest(folder, tag, target)
            if args.resolve_cli or args.install_cli:
                selection = select_cli(folder, manifest, target, assets, tag is not None)
                if args.resolve_cli:
                    print(json.dumps(selection, sort_keys=True))
                else:
                    install_cli(folder, selection, args.install_dir, tag is not None)
                return 0
            deploy(args, folder, tag, manifest, assets, zstd_supported)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, tarfile.TarError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"All-in-One installation failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
