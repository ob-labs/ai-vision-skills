import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import call, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_live_quickstart as quickstart


OLD = "v0.6.0-daily.20261122"
NEW = "v0.6.0-daily.20261123.2"
ARM64_MANIFEST = quickstart.PLATFORMS["arm64"][0]


def release(tag, published_at, *, personal=True, omitted=(), draft=False):
    product = json.dumps({"release_tag": tag, "source_repository": quickstart.REPO, "personal_edition": personal})
    architecture = json.dumps({"release_tag": tag, "platform": "linux/arm64", "image_id": "sha256:" + "1" * 64})
    assets = {name: b"test data" for bundle in quickstart.PLATFORMS.values() for name in bundle}
    assets.update({quickstart.MANIFEST: product.encode(), quickstart.INSTALLER: b"trusted installer",
                   ARM64_MANIFEST: architecture.encode()})
    for name in omitted:
        assets.pop(name)
    assets[quickstart.SUMS] = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n"
                                     for name, data in assets.items()).encode()
    metadata = {
        "id": 1, "tag_name": tag, "published_at": published_at, "draft": draft, "prerelease": True,
        "assets": [{"name": name, "state": "uploaded", "size": len(data),
                    "digest": "sha256:" + hashlib.sha256(data).hexdigest()} for name, data in assets.items()],
    }
    return metadata, assets


def downloader(*releases):
    listing = json.dumps([metadata for metadata, _ in releases]).encode()
    assets = {f"https://github.com/{quickstart.REPO}/releases/download/{metadata['tag_name']}/{name}": data
              for metadata, files in releases for name, data in files.items()}

    def read(url):
        if url == f"https://api.github.com/repos/{quickstart.REPO}/releases?per_page=100&page=1":
            return listing
        return assets[url]

    return read


class LiveQuickstartTests(unittest.TestCase):
    def test_resolves_latest_published_personal_daily_not_draft_alias_or_distributed(self):
        selected = release(NEW, "2026-11-23T19:00:00Z")
        fixtures = downloader(
            release(OLD, "2026-11-22T19:00:00Z"),
            release("v0.6.0-daily.20261124", "2026-11-24T19:00:00Z", personal=False),
            release("v0.6.0-daily.20261125", "2026-11-25T19:00:00Z", draft=True),
            release("daily", "2026-11-26T19:00:00Z"), selected,
        )
        with patch.object(quickstart, "download", side_effect=fixtures) as download:
            self.assertEqual(quickstart.latest_personal_daily()[0], NEW)
        self.assertEqual(len(download.call_args_list), 3)

    def test_does_not_fall_back_if_newest_personal_release_is_missing_an_architecture(self):
        fixtures = downloader(release(OLD, "2026-11-22T19:00:00Z"),
                              release(NEW, "2026-11-23T19:00:00Z", omitted=(ARM64_MANIFEST,)))
        with patch.object(quickstart, "download", side_effect=fixtures):
            with self.assertRaisesRegex(ValueError, f"{NEW} is incomplete: {ARM64_MANIFEST}"):
                quickstart.latest_personal_daily()

    def test_installer_must_match_official_sums_even_when_size_and_asset_digest_match(self):
        metadata, assets = release(NEW, "2026-11-23T19:00:00Z")
        asset = next(item for item in metadata["assets"] if item["name"] == quickstart.INSTALLER)
        tampered = b"tampered installer"
        asset.update(size=len(tampered), digest="sha256:" + hashlib.sha256(tampered).hexdigest())
        assets[quickstart.INSTALLER] = tampered
        with patch.object(quickstart, "download", side_effect=downloader((metadata, assets))), TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "install-all-in-one.py does not match the official SHA256SUMS"):
                quickstart.stage_installer(Path(tmp), "arm64")
            self.assertFalse((Path(tmp) / quickstart.INSTALLER).exists())

    def test_cleanup_removes_only_verified_resources(self):
        env = {"DOCKER_HOST": "unix:///var/run/docker.sock"}
        name = "smoke-fixture"
        owner = {quickstart.OWNER: name}
        objects = {
            "container": {"Config": {"Labels": owner}, "Id": "container-id"},
            "network": {"Labels": owner, "Id": "network-id"},
            "volume": {"Labels": {**owner, quickstart.RELEASE: NEW}},
        }
        with patch.object(quickstart, "exists", return_value=True), \
                patch.object(quickstart, "inspect", side_effect=lambda env, kind, name: objects[kind]), \
                patch.object(quickstart, "docker") as docker:
            quickstart.cleanup(env, name, NEW)
            self.assertEqual(docker.call_args_list, [call(env, "container", "rm", "--force", "container-id"),
                                                    call(env, "network", "rm", "network-id"),
                                                    call(env, "volume", "rm", name + "-data")])
            objects["volume"]["Labels"][quickstart.RELEASE] = OLD
            docker.reset_mock()
            with self.assertRaisesRegex(RuntimeError, "expected All-in-One ownership labels"):
                quickstart.cleanup(env, name, NEW)
            self.assertNotIn(call(env, "volume", "rm", name + "-data"), docker.call_args_list)
