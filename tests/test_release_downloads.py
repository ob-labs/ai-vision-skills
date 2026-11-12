"""Run the bundled discovery filter and POSIX installer against fake GitHub Releases.

Fixtures supply release pages and download bytes. The actual shell, jq, archive,
checksum, version check and replacement run without credentials or network.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tarfile
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("aivision-deploy", "aivision-quickstart", "aivision-trace", "aivision-metric")
LINUX_NEW = "delivery-v0.1.0-daily.20261108"
LINUX_ARM = "delivery-v0.1.0-daily.20261101"
MAC = "macos-codex-preview-v0.1.0-daily.20261108.1"
PRIVATE = "ob-labs/ai-vision-skills"
STABLE = "ob-labs/ai-vision-ob"
ORIGINAL = b"existing installed binary\n"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def cli_archive(version):
    binary = f"#!/bin/sh\nprintf '%s\\n' 'aiv {version}'\n".encode()
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        member = tarfile.TarInfo("aiv")
        member.mode = 0o755
        member.size = len(binary)
        archive.addfile(member, io.BytesIO(binary))
    return binary, output.getvalue()


def published(tag, *platforms, draft=False, unpublished=False, wrong_version=False,
              wrong_manifest=False, bad_checksum=False, rest_digests=True):
    stable = tag.startswith("v")
    companion = tag.startswith("macos-codex-preview-v")
    integrated_macos = tag.startswith("delivery-v") and "darwin-arm64" in platforms
    if companion:
        version = tag.removeprefix("macos-codex-preview-v").rsplit(".", 1)[0]
        base = "delivery-v" + version
    else:
        version = tag[1:] if stable else tag.removeprefix("delivery-v")
        base = tag
    binary, archive = cli_archive("9.9.9" if wrong_version else version)
    assets = {"aiv-" + platform + ".tar.gz": archive for platform in platforms if platform != "windows-x64"}
    macos_assets = {name: content for name, content in assets.items() if name.startswith("aiv-darwin-")}
    if companion or integrated_macos:
        macos_assets["macos-codex-preview.json"] = json.dumps({
            "profile": "macos-codex-preview", "release_tag": tag,
            "base_release": "delivery-v0.0.0-daily.20260101" if wrong_manifest else base,
            "client": {p: {"aiv_sha256": digest(binary)} for p in ("darwin/amd64", "darwin/arm64")},
            "assets": {name: {"sha256": digest(content)} for name, content in macos_assets.items()},
        }).encode()
        assets.update(macos_assets)
    if not (stable or companion):
        assets["release-manifest.json"] = json.dumps({
            "channel": "daily", "product_version": "9.9.9" if wrong_manifest else version,
            "cli_platforms": [p for p in platforms if p.startswith("linux-")],
            "delivery": {"release_tag": tag, "repository": PRIVATE},
        }).encode()
    assets["SHA256SUMS"] = "".join(f"{('0' * 64) if bad_checksum else digest(content)}  {name}\n"
                                  for name, content in assets.items() if not integrated_macos or name not in macos_assets).encode()
    if integrated_macos:
        assets["SHA256SUMS.macos"] = "".join(f"{digest(content)}  {name}\n" for name, content in macos_assets.items()).encode()
    if "windows-x64" in platforms:
        zip_output = io.BytesIO()
        executable = zipfile.ZipInfo("aiv.exe")
        executable.create_system = 3  # POSIX shell executable for the PowerShell fixture only.
        executable.external_attr = (stat.S_IFREG | 0o755) << 16
        with zipfile.ZipFile(zip_output, "w") as zipped:
            zipped.writestr(executable, binary)
        windows = zip_output.getvalue()
        assets["aiv-windows-x64.zip"] = windows
        assets["windows-preview.json"] = json.dumps({
            "release": {"tag": tag, "repository": PRIVATE}, "product_version": version,
            "client_platform": "windows-x64", "native_windows_qualified": False,
            "assets": {"aiv-windows-x64.zip": {"sha256": digest(windows), "size": len(windows)}},
        }).encode()
    # An unrelated product asset must not disqualify a compatible release.
    assets["optional-evidence.json"] = b"{}\n"
    return ({"id": tag, "tag_name": tag, "draft": draft, "prerelease": not stable,
             "published_at": None if unpublished else "2026-11-11T00:00:00Z",
             "assets": [{"id": name, "name": name, "state": "uploaded", "size": len(content),
                         "digest": f"sha256:{digest(content)}" if rest_digests else None}
                        for name, content in assets.items()]}, assets)


def read_selection(releases, platform, *, channel="daily", tag="", skill="aivision-quickstart"):
    selector = ROOT / "skills" / skill / "scripts/discover-cli.jq"
    output = subprocess.check_output(["jq", "-c", "--arg", "platform", platform,
                                     "--arg", "channel", channel, "--arg", "tag", tag,
                                     "-f", str(selector)], input=json.dumps(releases), text=True)
    return json.loads(output) if output else None


GH_FIXTURE = '''#!/usr/bin/env python3
import json, os, pathlib, shutil, sys
args = sys.argv[1:]
root = pathlib.Path(os.environ['AIV_TEST_ROOT'])
metadata = json.loads((root/'metadata.json').read_text())
with (root/'calls.jsonl').open('a') as log:
    log.write(json.dumps(args) + '\\n')
if args[0] == 'api':
    endpoint = args[-1]
    if endpoint.endswith('releases?per_page=100'):
        assert '--paginate' in args and '--slurp' in args
        print(json.dumps(metadata['pages']))
    else:
        assert '/releases/tags/' in endpoint
        tag = endpoint.rsplit('/', 1)[-1]
        print(json.dumps(metadata['exact'][tag]))
elif args[:2] == ['release', 'download']:
    destination = pathlib.Path(args[args.index('--dir') + 1])
    for index, arg in enumerate(args):
        if arg == '--pattern':
            name = args[index + 1]
            shutil.copyfile(root/'assets'/args[2]/name, destination/name)
else:
    sys.exit('unexpected gh operation')
'''


class DownloadRecipeTests(unittest.TestCase):
    def run_recipe(self, releases, *, skill="aivision-quickstart", mode="--resolve", tag="", channel="",
                   os_name="Linux", arch="x86_64", arm_hardware="0", changed_readback=False,
                   changed_download=None, powershell=None):
        with tempfile.TemporaryDirectory(prefix="aiv-discovery-") as temporary:
            root = Path(temporary)
            tools, installed = root / "tools", root / "install"
            tools.mkdir()
            installed.mkdir()
            binary = installed / ("aiv.exe" if powershell else "aiv")
            binary.write_bytes(ORIGINAL)
            exact = {release["tag_name"]: release for release, _ in releases}
            if changed_readback:
                exact = json.loads(json.dumps(exact))
                exact[tag]["assets"][0]["digest"] = "sha256:" + "0" * 64
            (root / "metadata.json").write_text(json.dumps({"pages": [[metadata] for metadata, _ in releases], "exact": exact}))
            for metadata, assets in releases:
                directory = root / "assets" / metadata["tag_name"]
                directory.mkdir(parents=True)
                for name, data in assets.items():
                    (directory / name).write_bytes(data)
            if changed_download:
                (root / "assets" / tag / changed_download).write_bytes(b"unexpected replacement\n")
            (tools / "uname").write_text('#!/bin/sh\ncase "$1" in -s) echo "$AIV_TEST_OS";; -m) echo "$AIV_TEST_ARCH";; esac\n')
            (tools / "sysctl").write_text('#!/bin/sh\n[ "$*" = "-n hw.optional.arm64" ] || exit 2\nprintf \'%s\\n\' "$AIV_TEST_HARDWARE"\n')
            (tools / "gh").write_text(GH_FIXTURE)
            for tool in tools.iterdir():
                tool.chmod(0o755)
            env = {k: v for k, v in os.environ.items() if not k.startswith("AIV_")}
            env.update(PATH=str(tools) + os.pathsep + env["PATH"], AIV_TAG=tag, AIV_CHANNEL=channel,
                       AIV_TEST_ROOT=str(root), AIV_TEST_OS=os_name, AIV_TEST_ARCH=arch,
                       AIV_TEST_HARDWARE=arm_hardware, AIV_INSTALL_DIR=str(installed))
            scripts = ROOT / "skills" / skill / "scripts"
            if powershell:
                # Only the hardware probe is substituted so the POSIX test host
                # can exercise the Windows recipient code with a shell fixture.
                hardware = "[System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()"
                script = (scripts / "install-cli.ps1").read_text()
                self.assertEqual(script.count(hardware), 1)
                helper = root / "install-cli.ps1"
                helper.write_text(script.replace(hardware, "'X64'"))
                shutil.copyfile(scripts / "discover-cli.jq", root / "discover-cli.jq")
                command = [powershell, "-NoProfile", "-NonInteractive", "-File", str(helper),
                           "-Mode", "Install" if mode == "--install" else "Resolve"]
            else:
                command = ["sh", str(scripts / "install-cli.sh"), mode]
            result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, timeout=20)
            calls_path = root / "calls.jsonl"
            calls = [json.loads(line) for line in calls_path.read_text().splitlines()] if calls_path.exists() else []
            return result, binary.read_bytes(), calls

    def test_discovery_uses_newest_compatible_linux_x64_release(self):
        releases = [published("delivery-v0.1.0-daily.20261110", "linux-arm64"),
                    published(LINUX_NEW, "linux-x64", "windows-x64"), published(LINUX_ARM, "linux-x64")]
        result, binary, calls = self.run_recipe(releases)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["tag"], LINUX_NEW)
        self.assertEqual(binary, ORIGINAL)
        self.assertFalse(any("aiv-linux-x64.tar.gz" in call for call in calls))

    def test_all_independent_helpers_match_and_install(self):
        for name in ("discover-cli.jq", "install-cli.sh", "install-cli.ps1"):
            self.assertEqual(len({(ROOT / "skills" / s / "scripts" / name).read_bytes() for s in SKILLS}), 1)
        for skill in SKILLS:
            with self.subTest(skill=skill):
                result, binary, calls = self.run_recipe([published(LINUX_NEW, "linux-x64")],
                                                        mode="--install", tag=LINUX_NEW, skill=skill)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(b"0.1.0-daily.20261108", binary)
                download, = [call for call in calls if call[:2] == ["release", "download"]]
                self.assertEqual(download[2], LINUX_NEW)
                self.assertIn("aiv-linux-x64.tar.gz", download)

    def test_macos_native_and_rosetta_select_the_verified_arm64_archive(self):
        releases = [published(LINUX_NEW, "linux-x64"), published(MAC, "darwin-x64", "darwin-arm64")]
        for arch, flag, target in (("arm64", "0", "darwin-arm64"), ("x86_64", "1", "darwin-arm64")):
            with self.subTest(arch=arch, flag=flag):
                result, binary, _ = self.run_recipe(releases, os_name="Darwin", arch=arch, arm_hardware=flag)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), {"repository": PRIVATE, "tag": MAC, "base_tag": LINUX_NEW,
                                 "product_version": "0.1.0-daily.20261108", "cli_platform": target, "profile": "macos",
                                 "package": f"aiv-{target}.tar.gz"})
                self.assertEqual(binary, ORIGINAL)
                result, binary, calls = self.run_recipe(releases, os_name="Darwin", arch=arch, arm_hardware=flag,
                                                        mode="--install", tag=MAC)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(b"0.1.0-daily.20261108", binary)
                self.assertTrue(any(f"aiv-{target}.tar.gz" in call for call in calls))

    def test_macos_prefers_integrated_release_and_uses_its_checksum_file(self):
        integrated = published(LINUX_NEW, "linux-x64", "darwin-arm64", "windows-x64")
        releases = [published(MAC, "darwin-arm64"), integrated]
        self.assertNotIn(b"aiv-darwin-arm64.tar.gz", integrated[1]["SHA256SUMS"])
        for arch, flag in (("arm64", "0"), ("x86_64", "1")):
            with self.subTest(arch=arch):
                result, binary, calls = self.run_recipe(releases, os_name="Darwin", arch=arch, arm_hardware=flag)
                self.assertEqual(result.returncode, 0, result.stderr)
                selected = json.loads(result.stdout)
                self.assertEqual((selected["tag"], selected["base_tag"], selected["profile"]), (LINUX_NEW, LINUX_NEW, "macos"))
                self.assertEqual(binary, ORIGINAL)
                download, = [call for call in calls if call[:2] == ["release", "download"]]
                self.assertIn("SHA256SUMS.macos", download)
                self.assertNotIn("SHA256SUMS", download)
        result, binary, calls = self.run_recipe([integrated], os_name="Darwin", arch="arm64", mode="--install", tag=LINUX_NEW)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"0.1.0-daily.20261108", binary)
        download, = [call for call in calls if call[:2] == ["release", "download"]]
        self.assertEqual(download[2], LINUX_NEW)
        self.assertIn("aiv-darwin-arm64.tar.gz", download)
        for platform in ("linux-x64", "windows-x64"):
            selected = read_selection([[integrated[0]]], platform)
            self.assertEqual(selected["assets"]["checksums"]["name"], "SHA256SUMS")

    def test_integrated_macos_verification_failures_preserve_existing_cli(self):
        for options, runtime in (({"wrong_manifest": True}, {}), ({}, {"changed_download": "SHA256SUMS.macos"})):
            with self.subTest(options=options, runtime=runtime):
                release = published(LINUX_NEW, "linux-x64", "darwin-arm64", **options)
                result, binary, _ = self.run_recipe([release], mode="--install", tag=LINUX_NEW,
                                                     os_name="Darwin", arch="arm64", **runtime)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(binary, ORIGINAL)

    def test_selects_windows_preview_without_requiring_its_zip_in_base_sums(self):
        release, assets = published(LINUX_NEW, "linux-x64", "windows-x64")
        self.assertNotIn(b"aiv-windows-x64.zip", assets["SHA256SUMS"])
        selected = read_selection([[release]], "windows-x64")
        self.assertEqual((selected["tag"], selected["base_tag"], selected["manifest"], selected["package"]),
                         (LINUX_NEW, LINUX_NEW, "windows-preview.json", "aiv-windows-x64.zip"))
        old, _ = published(LINUX_ARM, "windows-x64", rest_digests=False)
        self.assertIsNone(read_selection([[old]], "windows-x64"))

    @unittest.skipUnless(os.name == "posix" and shutil.which("pwsh"), "PowerShell fixture needs pwsh on POSIX")
    def test_powershell_replaces_existing_cli_after_exact_zip_verification(self):
        releases = [published(LINUX_NEW, "linux-x64", "windows-x64")]
        powershell = shutil.which("pwsh")
        result, binary, _ = self.run_recipe(releases, mode="--install", tag=LINUX_NEW, powershell=powershell)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"0.1.0-daily.20261108", binary)
        for tag, replacement in ((LINUX_NEW, "aiv-windows-x64.zip"), ("*", None)):
            with self.subTest(tag=tag):
                result, binary, _ = self.run_recipe(releases, mode="--install", tag=tag, powershell=powershell,
                                                    changed_download=replacement)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(binary, ORIGINAL)

    def test_numeric_order_ignores_publication_page_order_and_wrong_channel(self):
        tags = ["delivery-v0.1.0-daily.20261108.2", "delivery-v0.1.0-daily.20261108.10", "v9.0.0"]
        metadata = [published(tag, "linux-x64")[0] for tag in tags]
        self.assertEqual(read_selection([[metadata[0]], [metadata[2], metadata[1]]], "linux-x64")["tag"], tags[1])
        self.assertEqual(read_selection([metadata], "linux-x64", channel="stable")["tag"], tags[2])
        base = published(LINUX_NEW, "linux-x64")[0]
        macs = [published(MAC, "darwin-arm64")[0], published(MAC.rsplit(".", 1)[0] + ".10", "darwin-arm64")[0]]
        self.assertEqual(read_selection([[base, *macs]], "darwin-arm64")["tag"], macs[1]["tag_name"])

    def test_paused_hardware_rejects_even_an_explicit_compatible_archive(self):
        releases = [published(LINUX_ARM, "linux-arm64"), published(LINUX_NEW, "linux-x64"), published(MAC, "darwin-x64")]
        for system, arch, tag in (("Linux", "aarch64", LINUX_ARM), ("Darwin", "x86_64", MAC)):
            with self.subTest(system=system, arch=arch):
                result, binary, calls = self.run_recipe(releases, os_name=system, arch=arch, mode="--install", tag=tag)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(binary, ORIGINAL)
                self.assertEqual(calls, [])

    def test_selector_rejects_paused_hardware_in_both_channels(self):
        selector = ROOT / "skills/aivision-deploy/scripts/discover-cli.jq"
        for channel in ("daily", "stable"):
            for platform in ("linux-arm64", "darwin-x64", "windows-arm64"):
                with self.subTest(channel=channel, platform=platform):
                    result = subprocess.run(["jq", "-ce", "--arg", "channel", channel, "--arg", "platform", platform,
                                             "--arg", "tag", "", "-f", str(selector)], input="[]", text=True, capture_output=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Supported CLI platforms", result.stderr)

    def test_stable_release_install_preserves_legacy_checksum_path(self):
        tag = "v2.10.1"
        releases = [published("v2.9.9", "linux-x64"), published(tag, "linux-x64", rest_digests=False)]
        result, _, _ = self.run_recipe(releases, channel="stable")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["repository"], STABLE)
        self.assertEqual(json.loads(result.stdout)["tag"], tag)
        result, binary, _ = self.run_recipe(releases, mode="--install", tag=tag)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"2.10.1", binary)

    def test_no_implicit_install_or_unpublished_explicit_fallback(self):
        releases = [published(LINUX_NEW, "linux-x64", draft=True), published(LINUX_ARM, "linux-x64")]
        for tag in ("", "*", "__auto__", LINUX_NEW, "delivery-v0.1.0-daily.20261109"):
            with self.subTest(tag=tag):
                result, binary, calls = self.run_recipe(releases, mode="--install", tag=tag)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(binary, ORIGINAL)
                self.assertFalse(any(call[:2] == ["release", "download"] for call in calls))
        result, _, _ = self.run_recipe(releases)
        self.assertEqual(json.loads(result.stdout)["tag"], LINUX_ARM)

    def test_historical_safe_pin_and_retired_source_cli(self):
        retired = "delivery-v0.0.1-daily.20261028"
        safe = retired + ".2"
        releases = [published(retired, "linux-x64"), published(safe, "linux-x64")]
        result, _, _ = self.run_recipe(releases, mode="--install", tag=safe)
        self.assertEqual(result.returncode, 0, result.stderr)
        result, binary, _ = self.run_recipe(releases, mode="--install", tag=retired)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(binary, ORIGINAL)

    def test_macos_base_must_be_published_and_match_manifest(self):
        for releases in ([published(MAC, "darwin-arm64")],
                         [published(LINUX_NEW, "linux-x64", unpublished=True), published(MAC, "darwin-arm64")],
                         [published(LINUX_NEW, "linux-x64"), published(MAC, "darwin-arm64", wrong_manifest=True)]):
            result, binary, _ = self.run_recipe(releases, mode="--install", tag=MAC, os_name="Darwin", arch="arm64")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(binary, ORIGINAL)

    def test_integrity_failures_preserve_existing_binary(self):
        for fixture_options, runtime_options in (({"wrong_version": True}, {}), ({"wrong_manifest": True}, {}),
                                                 ({"bad_checksum": True}, {}), ({}, {"changed_readback": True}),
                                                 ({}, {"changed_download": "SHA256SUMS"}),
                                                 ({}, {"changed_download": "release-manifest.json"}),
                                                 ({}, {"changed_download": "aiv-linux-x64.tar.gz"})):
            with self.subTest(fixture_options=fixture_options, runtime_options=runtime_options):
                result, binary, _ = self.run_recipe([published(LINUX_NEW, "linux-x64", **fixture_options)],
                                                     mode="--install", tag=LINUX_NEW, **runtime_options)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(binary, ORIGINAL)


if __name__ == "__main__":
    unittest.main()
