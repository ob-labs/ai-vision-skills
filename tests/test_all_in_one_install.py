import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace


SCRIPT = (Path(__file__).resolve().parents[1] / "skills" / "aivision-deploy" /
          "scripts" / "install-all-in-one.py")
SPEC = importlib.util.spec_from_file_location("all_in_one_install", SCRIPT)
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)

EARLY = "all-in-one-preview-v0.1.0-daily.20261112"
LATEST = "all-in-one-preview-v0.1.0-daily.20261113"
ARM_LATEST = "all-in-one-preview-v0.1.0-daily.20261113.2"
BASE_RELEASE = "v0.1.0-daily.20261108"
AMD64 = "linux/amd64"
ARM64 = "linux/arm64"
AMD64_MANIFEST, AMD64_ARCHIVE, AMD64_CLI = installer.ASSETS[AMD64]
ARM64_MANIFEST, ARM64_ARCHIVE, ARM64_CLI = installer.ASSETS[ARM64]


def release(tag, published_at, release_id, *, draft=False, prerelease=True, missing=(), target=AMD64):
    return {
        "tag_name": tag,
        "id": release_id,
        "draft": draft,
        "prerelease": prerelease,
        "published_at": published_at,
        "assets": [
            {"name": name, "state": "uploaded", "size": 10, "digest": "sha256:" + "a" * 64}
            for name in (*installer.ASSETS[target], "install-all-in-one.py", "SHA256SUMS") if name not in missing
        ],
    }


class ReleaseDiscoveryTests(unittest.TestCase):
    def setUp(self):
        pages = [[
            release("v0.1.0-daily.20261118", "2026-11-18T10:00:00Z", 8),
            release("all-in-one-preview-v0.1.0-daily.20261117", "2026-11-17T10:00:00Z", 7,
                    draft=True),
            release("all-in-one-preview-v0.1.0-daily.20261116", "2026-11-16T10:00:00Z", 6,
                    prerelease=False),
            release("all-in-one-preview-v0.1.0-daily.20261115", "2026-11-15T10:00:00Z", 5,
                    missing=(AMD64_ARCHIVE,)),
            release(EARLY, "2026-11-12T10:00:00Z", 2, missing=(AMD64_CLI,)),
        ], [
            release(LATEST, "2026-11-13T10:00:00Z", 3, missing=(AMD64_CLI,)),
            release(ARM_LATEST, "2026-11-13T12:00:00Z", 4, target=ARM64),
            release("all-in-one-preview-v0.1.0-daily.20261119", "2026-11-19T10:00:00Z", 9,
                    target=ARM64, missing=(ARM64_CLI,)),
        ]]
        fixture = patch.object(installer, "output", return_value=json.dumps(pages))
        self.addCleanup(fixture.stop)
        self.output = fixture.start()

    def test_discovery_filters_release_profile_and_checks_all_pages(self):
        self.assertEqual(installer.resolve_release(None, AMD64), LATEST)
        self.output.assert_called_once_with(
            "gh", "api", "--hostname", "github.com", "--paginate", "--slurp",
            "repos/antgroup/ai-vision/releases?per_page=100",
        )

    def test_exact_tag_selects_older_release_and_never_falls_back(self):
        self.assertEqual(installer.resolve_release(EARLY, AMD64), EARLY)
        with self.assertRaisesRegex(ValueError, "No published All-in-One release for linux/amd64"):
            installer.resolve_release("all-in-one-preview-v0.1.0-daily.20261115", AMD64)

    def test_arm64_ignores_x86_release_and_incomplete_arm_release(self):
        self.assertEqual(installer.resolve_release(None, ARM64), ARM_LATEST)
        with self.assertRaisesRegex(ValueError, "No published All-in-One release for linux/arm64"):
            installer.resolve_release(LATEST, ARM64)


class PlatformTests(unittest.TestCase):
    def test_normalizes_native_linux_machine_names(self):
        for machine, target in (("aarch64", ARM64), ("arm64", ARM64), ("x86_64", AMD64), ("amd64", AMD64)):
            with self.subTest(machine=machine):
                self.assertEqual(installer.linux_platform("Linux", machine), target)
        with self.assertRaisesRegex(ValueError, "requires Linux"):
            installer.linux_platform("Darwin", "arm64")

    def test_docker_mismatch_is_rejected_before_any_mutation(self):
        with patch.object(installer, "output", return_value="linux/x86_64") as output, patch.object(
            installer.subprocess, "run",
        ) as run:
            with self.assertRaisesRegex(ValueError, "matching local linux/arm64 Docker daemon"):
                installer.preflight(SimpleNamespace(name="aiv-trial"), ARM64)
        output.assert_called_once_with("docker", "info", "--format", "{{.OSType}}/{{.Architecture}}")
        run.assert_not_called()

    def test_local_port_conflict_is_reported_before_archive_work(self):
        args = SimpleNamespace(name="aiv-trial", web_port=5174, otlp_port=4318)
        with patch.object(installer, "output", side_effect=["linux/aarch64", ""]) as docker, patch.object(
            installer.socket, "socket",
        ) as socket:
            socket.return_value.__enter__.return_value.bind.side_effect = OSError("in use")
            with self.assertRaisesRegex(ValueError, "Cannot bind local port 5174"):
                installer.preflight(args, ARM64)
            self.assertEqual(docker.call_count, 2)

    def test_docker_server_version_controls_compression(self):
        args = SimpleNamespace(name="aiv-trial", web_port=5174, otlp_port=4318)
        for version, expected in (("26.1.3", True), ("23.0.0", True), ("20.10.24", False), ("unknown", False)):
            with self.subTest(version=version), patch.object(
                installer, "output", side_effect=["linux/amd64", "", version],
            ), patch.object(installer.socket, "socket"):
                self.assertEqual(installer.preflight(args, AMD64), expected)


class PackageTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.folder = Path(directory.name)
        self.archive = self.folder / AMD64_ARCHIVE
        content = b"fixture image archive"
        self.archive.write_bytes(content)
        self.manifest = {
            "schema_version": 1,
            "profile": "all-in-one-preview",
            "platform": AMD64,
            "release_tag": LATEST,
            "base_release": BASE_RELEASE,
            "archive": AMD64_ARCHIVE,
            "archive_bytes": len(content),
            "archive_sha256": hashlib.sha256(content).hexdigest(),
            "image_id": "sha256:" + "a" * 64,
            "image_tag": "aiv-all-in-one:fixture-amd64",
        }
        (self.folder / AMD64_MANIFEST).write_text(json.dumps(self.manifest), encoding="utf-8")
        (self.folder / installer.SUMS).write_text(f"{self.manifest['archive_sha256']}  {AMD64_ARCHIVE}\n")

    def test_verified_package_keeps_the_image_identity_and_base_release(self):
        self.assertEqual(installer.read_manifest(self.folder, LATEST, AMD64), self.manifest)
        self.assertEqual(installer.image_archive(self.folder, self.manifest, None, "auto", True)[0], AMD64_ARCHIVE)

    def test_keeps_original_base_tag_in_a_trusted_local_bundle(self):
        manifest = {**self.manifest, "base_release": f"delivery-{BASE_RELEASE}"}
        (self.folder / AMD64_MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
        self.assertEqual(installer.read_manifest(self.folder, None, AMD64), manifest)

    def test_rejects_wrong_pinned_release_and_changed_archive(self):
        with self.assertRaisesRegex(ValueError, "selected All-in-One release"):
            installer.read_manifest(self.folder, EARLY, AMD64)
        self.archive.write_bytes(b"X" * self.manifest["archive_bytes"])
        with self.assertRaisesRegex(ValueError, "tar.gz SHA-256"):
            installer.image_archive(self.folder, self.manifest, None, "auto", True)

    def test_arm64_requires_a_matching_verified_cli_and_its_own_image(self):
        cli = self.folder / ARM64_CLI
        content = b"fixture CLI archive"
        cli.write_bytes(content)
        (self.folder / ARM64_ARCHIVE).write_bytes(self.archive.read_bytes())
        manifest_path = self.folder / ARM64_MANIFEST
        manifest = {
            **self.manifest, "platform": ARM64, "release_tag": ARM_LATEST, "archive": ARM64_ARCHIVE,
            "agent_cli": {
                "archive": ARM64_CLI,
                "archive_bytes": len(content),
                "archive_sha256": hashlib.sha256(content).hexdigest(),
                "binary_sha256": "b" * 64,
                "version": "0.1.0-daily.20261108",
            },
        }
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertEqual(installer.read_manifest(self.folder, ARM_LATEST, ARM64), manifest)
        installer.verify_client_archive(self.folder, manifest)
        cli.write_bytes(b"X" * len(content))
        with self.assertRaisesRegex(ValueError, "aiv-linux-arm64.tar.gz SHA-256"):
            installer.verify_client_archive(self.folder, manifest)
        manifest["agent_cli"]["version"] = "0.1.0-daily.20261112"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "matching Agent CLI"):
            installer.read_manifest(self.folder, ARM_LATEST, ARM64)
        manifest["platform"] = AMD64
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "selected All-in-One release"):
            installer.read_manifest(self.folder, ARM_LATEST, ARM64)

    def test_zstd_preferred_for_modern_docker_with_usable_archive(self):
        zstd = Path(AMD64_ARCHIVE).with_suffix(".zst").name
        data = b"zstd fixture"
        (self.folder / zstd).write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        manifest = {**self.manifest, "zstd_archive": zstd, "zstd_archive_sha256": digest, "zstd_archive_bytes": len(data)}
        (self.folder / AMD64_MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
        self.assertEqual(installer.read_manifest(self.folder, LATEST, AMD64), manifest)
        with (self.folder / installer.SUMS).open("a", encoding="ascii") as checksums:
            checksums.write(f"{digest}  {zstd}\n")
        self.assertEqual(installer.image_archive(self.folder, manifest, None, "auto", True)[0], zstd)
        self.assertEqual(installer.image_archive(self.folder, manifest, None, "gzip", True)[0], AMD64_ARCHIVE)
        self.assertEqual(installer.image_archive(self.folder, manifest, None, "auto", False)[0], AMD64_ARCHIVE)
        with self.assertRaisesRegex(ValueError, "outside the zstd support threshold"):
            installer.image_archive(self.folder, manifest, None, "zstd", False)
        (self.folder / zstd).unlink()
        self.assertEqual(installer.image_archive(self.folder, manifest, None, "auto", True)[0], AMD64_ARCHIVE)
        with self.assertRaisesRegex(ValueError, "no zstd archive available"):
            installer.image_archive(self.folder, manifest, None, "zstd", True)

    def test_partial_or_wrong_architecture_zstd_manifest_is_rejected(self):
        wrong = {**self.manifest, "zstd_archive": "aiv-all-in-one-linux-arm64.tar.zst"}
        (self.folder / AMD64_MANIFEST).write_text(json.dumps(wrong), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid zstd image archive"):
            installer.read_manifest(self.folder, LATEST, AMD64)

    def test_zstd_authenticated_identity_checked_before_download(self):
        name = "aiv-all-in-one-linux-amd64.tar.zst"
        manifest = {**self.manifest, "zstd_archive": name, "zstd_archive_sha256": "a" * 64, "zstd_archive_bytes": 25}
        assets = {name: {"digest": "sha256:" + "b" * 64, "size": 25}}
        with self.assertRaisesRegex(ValueError, "differs from the manifest"):
            installer.image_archive(self.folder, manifest, assets, "auto", True)

    def test_corrupt_cache_is_replaced_and_verified_cache_is_reused(self):
        data = self.archive.read_bytes()
        name, digest, size = (self.manifest[field] for field in ("archive", "archive_sha256", "archive_bytes"))
        cache = self.folder / "cache"
        cached = cache / digest / name
        cached.parent.mkdir(parents=True)
        cached.write_bytes(b"X" * size)

        def download(folder, tag, requested):
            self.assertEqual((tag, requested), (LATEST, name))
            (folder / requested).write_bytes(data)

        with patch.object(installer, "download", side_effect=download) as fetch:
            self.assertEqual(installer.cached_image_archive(cache, LATEST, name, digest, size), cached)
            self.assertEqual(installer.cached_image_archive(cache, LATEST, name, digest, size), cached)
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(cached.read_bytes(), data)


class CliTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.folder = Path(directory.name)
        self.base_manifest = {"release_tag": LATEST, "base_release": BASE_RELEASE}

    def selection(self, target):
        _, _, name = installer.ASSETS[target]
        archive = self.folder / name
        binary = b"\x7fELF\x02\x01\x01" + b"\x00" * 11 + installer.ELF_MACHINES[target].to_bytes(2, "little")
        with tarfile.open(archive, "w:gz") as bundle:
            info = tarfile.TarInfo("aiv")
            info.size = len(binary)
            bundle.addfile(info, io.BytesIO(binary))
        digest = installer.file_sha256(archive)
        (self.folder / installer.SUMS).write_text(f"{digest}  {name}\n", encoding="ascii")
        cli = {"archive": name, "archive_bytes": archive.stat().st_size, "archive_sha256": digest,
               "binary_sha256": hashlib.sha256(binary).hexdigest(), "version": "0.1.0-daily.20261108"}
        return {**self.base_manifest, "agent_cli": cli}

    def test_bundled_cli_uses_its_own_preview_asset_for_both_architectures(self):
        for target in (AMD64, ARM64):
            with self.subTest(target=target):
                manifest = self.selection(target)
                cli = manifest["agent_cli"]
                assets = {cli["archive"]: {"digest": "sha256:" + cli["archive_sha256"],
                                           "size": cli["archive_bytes"]}}
                selection = installer.select_cli(self.folder, manifest, target, assets, True)
                self.assertEqual(selection["release_tag"], LATEST)
                self.assertEqual(selection["platform"], target)
                self.assertEqual(selection["archive"], installer.ASSETS[target][2])
                assets[cli["archive"]]["size"] += 1
                with self.assertRaisesRegex(ValueError, "differs from the manifest"):
                    installer.select_cli(self.folder, manifest, target, assets, True)

    def test_legacy_cli_checks_authenticated_base_metadata_and_checksums(self):
        manifest = self.selection(AMD64)
        cli = manifest["agent_cli"]
        sums = self.folder / installer.SUMS
        assets = {
            cli["archive"]: {"digest": "sha256:" + cli["archive_sha256"], "size": cli["archive_bytes"]},
            installer.SUMS: {"digest": "sha256:" + installer.file_sha256(sums), "size": sums.stat().st_size},
        }
        with patch.object(installer, "published_assets", return_value=assets) as published, patch.object(
            installer, "download",
        ) as download:
            selection = installer.select_cli(self.folder, self.base_manifest, AMD64, {}, True)
        published.assert_called_once_with(BASE_RELEASE)
        download.assert_called_once_with(self.folder, BASE_RELEASE, installer.SUMS)
        self.assertEqual(selection["release_tag"], BASE_RELEASE)
        self.assertEqual(selection["archive_sha256"], cli["archive_sha256"])
        self.assertEqual(selection["version"], cli["version"])

    def test_local_install_is_atomic_and_preserves_prior_binary_on_mismatch(self):
        manifest = self.selection(ARM64)
        selection = installer.select_cli(self.folder, manifest, ARM64, {}, False)
        directory = self.folder / "bin"
        directory.mkdir()
        installed = directory / "aiv"
        installed.write_text("prior binary")
        with patch.object(installer, "output", return_value="aiv fixture-unmatched"):
            with self.assertRaisesRegex(ValueError, "version differs"):
                installer.install_cli(self.folder, selection, directory, False)
        self.assertEqual(installed.read_text(), "prior binary")
        self.assertEqual(list(directory.iterdir()), [installed])
        with patch.object(installer, "output", return_value="aiv " + selection["version"]) as version:
            installer.install_cli(self.folder, selection, directory, False)
        self.assertEqual(version.call_args.args[1:], ("--version",))
        self.assertEqual(installer.file_sha256(installed), selection["binary_sha256"])

    def test_wrong_elf_architecture_is_never_executed(self):
        manifest = self.selection(AMD64)
        selection = installer.select_cli(self.folder, manifest, ARM64, {}, False)
        with patch.object(installer, "output") as version:
            with self.assertRaisesRegex(ValueError, "does not match linux/arm64"):
                installer.install_cli(self.folder, selection, self.folder / "bin", False)
        version.assert_not_called()


class VolumeTests(unittest.TestCase):
    def test_reuse_requires_same_owner_and_same_preview_release(self):
        expected = {installer.OWNER: "aiv-trial", installer.RELEASE: LATEST}
        for actual, message in (
            (expected, None),
            ({installer.OWNER: "another-trial", installer.RELEASE: LATEST}, "another deployment"),
            ({installer.OWNER: "aiv-trial", installer.RELEASE: EARLY}, "different All-in-One release"),
        ):
            with self.subTest(actual=actual), patch.object(
                installer, "output", side_effect=["aiv-trial-data", json.dumps(actual)],
            ):
                if message is None:
                    self.assertTrue(installer.verify_resource("volume", "aiv-trial-data", expected))
                else:
                    with self.assertRaisesRegex(ValueError, message):
                        installer.verify_resource("volume", "aiv-trial-data", expected)


class SampleTraceTests(unittest.TestCase):
    def test_sample_uses_owned_instance_ports_and_volume_release(self):
        labels = {installer.OWNER: "aiv-trial"}
        ports = {"5174/tcp": [{"HostIp": "127.0.0.1", "HostPort": "55174"}],
                 "4318/tcp": [{"HostIp": "127.0.0.1", "HostPort": "54318"}]}
        mounts = [{"Type": "volume", "Name": "aiv-trial-data", "Destination": "/data"}]
        response = "\n".join(json.dumps(part) for part in (labels, "healthy", ports, mounts))
        volume = json.dumps({**labels, installer.RELEASE: LATEST})
        with patch.object(installer, "output", side_effect=[response, volume]):
            self.assertEqual(installer.sample_instance("aiv-trial"), (LATEST, [55174, 54318]))
        with patch.object(installer, "output", return_value=response) as inspect:
            with self.assertRaisesRegex(ValueError, "not a healthy All-in-One container"):
                installer.sample_instance("another-installation")
            inspect.assert_called_once()

    def test_sample_online_requires_the_running_instances_pinned_release(self):
        args = SimpleNamespace(name="aiv-trial", tag=EARLY, from_dir=None)
        with patch.object(installer, "sample_instance", return_value=(LATEST, [55174, 54318])), patch.object(
            installer, "published_assets",
        ) as published:
            with self.assertRaisesRegex(ValueError, "Select that exact release"):
                installer.sample_trace(args, AMD64)
            published.assert_not_called()
