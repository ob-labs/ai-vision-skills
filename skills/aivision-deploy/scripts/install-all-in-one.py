#!/usr/bin/env python3
"""Install the AI Vision All-in-One preview on a supported local Linux Docker host."""

import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tarfile
from tempfile import NamedTemporaryFile, TemporaryDirectory
import time


REPO = "ob-labs/ai-vision-skills"
PROFILE = "all-in-one-preview"
TAG = re.compile(r"all-in-one-preview-v\d+\.\d+\.\d+-daily\.\d{8}(?:\.\d+)?")
BASE = re.compile(r"delivery-v\d+\.\d+\.\d+-daily\.\d{8}(?:\.\d+)?")
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
    pages = json.loads(output(
        "gh", "api", "--hostname", "github.com", "--paginate", "--slurp",
        f"repos/{REPO}/releases?per_page=100",
    ))
    releases = [
        release for page in pages for release in page
        if TAG.fullmatch(release["tag_name"]) and (tag is None or tag == release["tag_name"])
        and release["prerelease"] and not release["draft"] and release["published_at"]
        and required_assets <= {asset["name"] for asset in release["assets"] if asset["state"] == "uploaded"}
    ]
    if not releases:
        raise ValueError(f"No published All-in-One preview for {target} matches the request.")
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
    if (
        manifest.get("schema_version") != 1
        or manifest.get("profile") != PROFILE
        or manifest.get("platform") != target
        or not TAG.fullmatch(manifest["release_tag"])
        or (selected is not None and manifest["release_tag"] != selected)
        or not BASE.fullmatch(manifest["base_release"])
        or manifest.get("archive") != archive
        or not SHA256.fullmatch(manifest["archive_sha256"])
        or not require_size(manifest.get("archive_bytes"))
        or not re.fullmatch(r"sha256:[a-f0-9]{64}", manifest["image_id"])
        or not re.fullmatch(r"aiv-all-in-one:[a-z0-9][a-z0-9._-]*", manifest["image_tag"])
    ):
        raise ValueError("The manifest does not describe the selected All-in-One preview.")

    if target == "linux/arm64" or "agent_cli" in manifest:
        client = manifest.get("agent_cli")
        if (
            not isinstance(client, dict)
            or client.get("archive") != client_archive
            or f"delivery-v{client.get('version')}" != manifest["base_release"]
            or not SHA256.fullmatch(client.get("archive_sha256", ""))
            or not SHA256.fullmatch(client.get("binary_sha256", ""))
            or not require_size(client.get("archive_bytes"))
        ):
            raise ValueError("The preview manifest is missing a matching Agent CLI.")
    return manifest


def verify_package(folder, selected, target):
    manifest = read_manifest(folder, selected, target)
    verify_file(folder / manifest["archive"], manifest["archive_sha256"], manifest["archive_bytes"])
    if "agent_cli" in manifest:
        client = manifest["agent_cli"]
        verify_file(folder / client["archive"], client["archive_sha256"], client["archive_bytes"])
    return manifest


def preview_manifest(folder, tag, target):
    name = ASSETS[target][0]
    if tag is None:
        verify_file(folder / name, sum_for(folder, name))
        return read_manifest(folder, None, target), {}

    assets = published_assets(tag)
    digest, size = asset_identity(assets, name)
    download(folder, tag, name)
    verify_file(folder / name, digest, size)
    return read_manifest(folder, tag, target), assets


def verify_asset_metadata(assets, name, digest, size):
    if asset_identity(assets, name) != (digest, size):
        raise ValueError(f"Authenticated GitHub identity for {name} differs from the manifest.")


def select_cli(folder, manifest, target, assets, online):
    preview_tag = manifest["release_tag"]
    client = manifest.get("agent_cli")
    if client is not None:
        if online:
            verify_asset_metadata(assets, client["archive"], client["archive_sha256"], client["archive_bytes"])
        release_tag = preview_tag
    else:
        if not online:
            raise ValueError("This legacy x86-64 preview uses a separate CLI release. Use --tag for CLI access.")
        release_tag = manifest["base_release"]
        cli_assets = published_assets(release_tag)
        archive = ASSETS[target][2]
        digest, size = asset_identity(cli_assets, archive)
        download(folder, release_tag, SUMS)
        verify_file(folder / SUMS, *asset_identity(cli_assets, SUMS))
        if sum_for(folder, archive) != digest:
            raise ValueError("The base CLI archive checksum differs from authenticated GitHub metadata.")
        client = {"archive": archive, "archive_sha256": digest, "archive_bytes": size,
                  "version": release_tag[len("delivery-v"):]}
    return {**client, "platform": target, "preview_tag": preview_tag, "release_tag": release_tag,
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
    target = manifest["platform"]
    docker_system, _, docker_architecture = output("docker", "info", "--format", "{{.OSType}}/{{.Architecture}}").partition("/")
    if linux_platform(docker_system, docker_architecture) != target:
        raise ValueError(f"A matching local {target} Docker daemon is required.")
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
    if image_tag in known_tags and output("docker", "image", "inspect", "--format", image_ref, image_tag) != f"{image} {target}":
        raise ValueError(f"Docker image tag {image_tag} already points to different bytes.")
    subprocess.run(["docker", "load", "--input", str(folder / manifest["archive"])], check=True)
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
                print(f"Preview: {manifest['release_tag']} ({target}). Base release: {manifest['base_release']}.")
                print(f"Matching Agent CLI: {client['archive']} (aiv {client['version']}) from this preview.")
            else:
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
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument("--resolve", action="store_true", help="Print the compatible published preview tag.")
    operation.add_argument("--resolve-cli", action="store_true", help="Print the matching Agent CLI selection as JSON.")
    operation.add_argument("--install-cli", action="store_true", help="Install the matching Agent CLI without Docker.")
    parser.add_argument("--install-dir", type=Path, default=Path("~/.local/bin"), help="Directory for --install-cli.")
    parser.add_argument("--name", default="aiv-all-in-one", help="Docker resource name prefix.")
    parser.add_argument("--web-port", type=int, default=5174)
    parser.add_argument("--otlp-port", type=int, default=4318)
    parser.add_argument("--timeout", type=int, default=300, help="Readiness timeout in seconds.")
    args = parser.parse_args()

    try:
        target = linux_platform(platform.system(), platform.machine())
        if args.tag is not None and not TAG.fullmatch(args.tag):
            raise ValueError("Specify an exact All-in-One preview tag.")
        if args.resolve and args.from_dir:
            raise ValueError("--resolve selects a published preview. Use --resolve-cli for a local CLI selection.")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,47}", args.name):
            raise ValueError("Use a name of 2–48 lowercase letters, digits or hyphens, starting with a letter or digit.")
        ports = {args.web_port, args.otlp_port}
        if len(ports) != 2 or min(ports) < 1 or max(ports) > 65535 or args.timeout < 1:
            raise ValueError("Specify distinct TCP ports in 1–65535 and a positive readiness timeout.")

        tag = None if args.from_dir else resolve_release(args.tag, target)
        if args.resolve:
            print(tag)
            return 0
        with (nullcontext(args.from_dir) if args.from_dir else TemporaryDirectory(prefix="aiv-all-in-one-")) as directory:
            folder = Path(directory).resolve()
            manifest, assets = preview_manifest(folder, tag, target)
            if args.resolve_cli or args.install_cli:
                selection = select_cli(folder, manifest, target, assets, tag is not None)
                if args.resolve_cli:
                    print(json.dumps(selection, sort_keys=True))
                else:
                    install_cli(folder, selection, args.install_dir, tag is not None)
                return 0
            if tag:
                print(f"Downloading {tag}...", flush=True)
                archive = manifest["archive"]
                verify_asset_metadata(assets, archive, manifest["archive_sha256"], manifest["archive_bytes"])
                names = [archive]
                if "agent_cli" in manifest:
                    client = manifest["agent_cli"]
                    verify_asset_metadata(assets, client["archive"], client["archive_sha256"], client["archive_bytes"])
                    names.append(client["archive"])
                download(folder, tag, *names)
            manifest = verify_package(folder, tag, target)
            install(args, folder, manifest)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, tarfile.TarError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"All-in-One installation failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
