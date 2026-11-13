import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = (Path(__file__).resolve().parents[1] / "skills" / "aivision-deploy" /
          "scripts" / "install-all-in-one.py")
SPEC = importlib.util.spec_from_file_location("all_in_one_install", SCRIPT)
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)

EARLY = "all-in-one-preview-v0.1.0-daily.20261112"
LATEST = "all-in-one-preview-v0.1.0-daily.20261113"
BASE_RELEASE = "delivery-v0.1.0-daily.20261108"


def release(tag, published_at, release_id, *, draft=False, prerelease=True, missing=()):
    return {
        "tag_name": tag,
        "id": release_id,
        "draft": draft,
        "prerelease": prerelease,
        "published_at": published_at,
        "assets": [
            {"name": name, "state": "uploaded", "size": 10, "digest": "sha256:" + "a" * 64}
            for name in installer.RELEASE_FILES if name not in missing
        ],
    }


class ReleaseDiscoveryTests(unittest.TestCase):
    def setUp(self):
        pages = [[
            release("delivery-v0.1.0-daily.20261118", "2026-11-18T10:00:00Z", 8),
            release("all-in-one-preview-v0.1.0-daily.20261117", "2026-11-17T10:00:00Z", 7,
                    draft=True),
            release("all-in-one-preview-v0.1.0-daily.20261116", "2026-11-16T10:00:00Z", 6,
                    prerelease=False),
            release("all-in-one-preview-v0.1.0-daily.20261115", "2026-11-15T10:00:00Z", 5,
                    missing=(installer.ARCHIVE,)),
            release(EARLY, "2026-11-12T10:00:00Z", 2),
        ], [release(LATEST, "2026-11-13T10:00:00Z", 3)]]
        fixture = patch.object(installer, "output", return_value=json.dumps(pages))
        self.addCleanup(fixture.stop)
        self.output = fixture.start()

    def test_discovery_filters_release_profile_and_checks_all_pages(self):
        self.assertEqual(installer.resolve_release(None), LATEST)
        self.output.assert_called_once_with(
            "gh", "api", "--hostname", "github.com", "--paginate", "--slurp",
            "repos/ob-labs/ai-vision-skills/releases?per_page=100",
        )

    def test_exact_tag_selects_older_release_and_never_falls_back(self):
        self.assertEqual(installer.resolve_release(EARLY), EARLY)
        with self.assertRaisesRegex(ValueError, "No published Linux x86-64"):
            installer.resolve_release("all-in-one-preview-v0.1.0-daily.20261115")


class PackageTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.folder = Path(directory.name)
        self.archive = self.folder / installer.ARCHIVE
        content = b"fixture image archive"
        self.archive.write_bytes(content)
        self.manifest = {
            "schema_version": 1,
            "profile": "all-in-one-preview",
            "platform": "linux/amd64",
            "release_tag": LATEST,
            "base_release": BASE_RELEASE,
            "archive": installer.ARCHIVE,
            "archive_bytes": len(content),
            "archive_sha256": hashlib.sha256(content).hexdigest(),
            "image_id": "sha256:" + "a" * 64,
            "image_tag": "aiv-all-in-one:fixture-amd64",
        }
        (self.folder / installer.MANIFEST).write_text(json.dumps(self.manifest), encoding="utf-8")

    def test_verified_package_keeps_the_image_identity_and_base_release(self):
        self.assertEqual(installer.verify_package(self.folder, LATEST), self.manifest)

    def test_rejects_wrong_pinned_release_and_changed_archive(self):
        with self.assertRaisesRegex(ValueError, "selected All-in-One preview"):
            installer.verify_package(self.folder, EARLY)
        self.archive.write_bytes(b"X" * self.manifest["archive_bytes"])
        with self.assertRaisesRegex(ValueError, "archive SHA-256"):
            installer.verify_package(self.folder, LATEST)


class VolumeTests(unittest.TestCase):
    def test_reuse_requires_same_owner_and_same_preview_release(self):
        expected = {installer.OWNER: "aiv-trial", installer.RELEASE: LATEST}
        for actual, message in (
            (expected, None),
            ({installer.OWNER: "another-trial", installer.RELEASE: LATEST}, "another deployment"),
            ({installer.OWNER: "aiv-trial", installer.RELEASE: EARLY}, "different preview"),
        ):
            with self.subTest(actual=actual), patch.object(
                installer, "output", side_effect=["aiv-trial-data", json.dumps(actual)],
            ):
                if message is None:
                    self.assertTrue(installer.verify_resource("volume", "aiv-trial-data", expected))
                else:
                    with self.assertRaisesRegex(ValueError, message):
                        installer.verify_resource("volume", "aiv-trial-data", expected)
