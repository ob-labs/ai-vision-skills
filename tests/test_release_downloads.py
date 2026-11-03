"""Run each standalone shell recipe against local Release transport fixtures.

Only curl/GitHub transport and uname are replaced. Shell, JSON validation, tar,
checksums, executable version checks and atomic replacement remain real.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PRODUCT_REPOSITORY = "ob-labs/ai-vision-ob"
HISTORICAL_REPOSITORY = "ob-labs/ai-vision-skills"
NEW_VERSION = "0.1.0-daily.20990101.2"  # fixture, not a publication claim
SKILLS = ("aivision-deploy", "aivision-quickstart", "aivision-trace", "aivision-metric")
HISTORICAL_VERSIONS = ("0.0.1-daily.20261028.2", "0.0.1-daily.20261029", "0.1.0-daily.20261101")


def recipe(skill):
    text = (ROOT / "skills" / skill / "reference/install-cli.md").read_text()
    return next(block for block in re.findall(r"```bash\n(.*?)\n```", text, re.S)
                if "AIV_TAG=" in block and "AIV_REPOSITORY=" in block)


class DownloadRecipeTests(unittest.TestCase):
    def run_recipe(self, skill="aivision-quickstart", *, arch="aarch64", os_name="Linux",
                   version=NEW_VERSION, tag=None, repository=None, historical=False,
                   anonymous=True, authenticated=False, missing=None, extra=False,
                   draft=False, prerelease=None, manifest_changes=None,
                   wrong_binary_version=False, bad_checksum=False, unset_tag=False, save_release=False, existing_release=False):
        with tempfile.TemporaryDirectory(prefix="aiv-catalog-download-") as temporary:
            root = Path(temporary)
            tools, assets, installed = root / "tools", root / "assets", root / "install"
            tools.mkdir(); assets.mkdir(); installed.mkdir()
            original = b"existing installed binary\n"
            (installed / "aiv").write_bytes(original)
            release_repository = HISTORICAL_REPOSITORY if historical else PRODUCT_REPOSITORY
            release_tag = ("delivery-v" if historical else "v") + version
            cli_platforms = ["linux-x64"] if historical and version == HISTORICAL_VERSIONS[0] else ["linux-x64", "linux-arm64"]
            if not historical:
                cli_platforms += ["darwin-x64", "darwin-arm64"]
            for platform in cli_platforms:
                binary_version = "0.0.1" if wrong_binary_version else version
                payload = f"#!/bin/sh\nprintf '%s\\n' 'aiv {binary_version}'\n".encode()
                with tarfile.open(assets / f"aiv-{platform}.tar.gz", "w:gz") as archive:
                    member = tarfile.TarInfo("aiv"); member.mode = 0o755; member.size = len(payload)
                    archive.addfile(member, io.BytesIO(payload))
            channel = "daily" if "-daily." in version else "stable"
            manifest = {"source_repository": PRODUCT_REPOSITORY, "release_tag": release_tag,
                        "product_version": version, "channel": channel,
                        "cli_platforms": cli_platforms, "images": {"signoz-ob": "ghcr.io/ob-labs/signoz-ob@sha256:" + "1" * 64}}
            if historical:
                manifest.pop("release_tag")
                manifest["delivery"] = {"repository": HISTORICAL_REPOSITORY, "release_tag": release_tag,
                                        "catalog_sha": "c" * 40}
            manifest.update(manifest_changes or {})
            (assets / "release-manifest.json").write_text(json.dumps(manifest))
            for name in ["install-aiv.sh", "release-images.vars.yaml", "release-seekdb.vars.yaml"]:
                (assets / name).write_text("fixture\n")
            if extra:
                (assets / "release-plan.json").write_bytes(b"product-owned asset\n")
            (assets / "SHA256SUMS").write_text("".join(
                f"{('0' * 64) if bad_checksum is True or bad_checksum == p.name else hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n"
                for p in sorted(assets.iterdir()) if p.name != "SHA256SUMS"))
            if missing:
                (assets / missing).unlink()
            base = f"https://github.com/{release_repository}/releases"
            metadata = {"tag_name": release_tag, "draft": draft,
                        "prerelease": channel == "daily" if prerelease is None else prerelease,
                        "published_at": "2099-01-01T01:02:03Z", "html_url": f"{base}/tag/{release_tag}",
                        "assets": [{"name": p.name, "browser_download_url": f"{base}/download/{release_tag}/{p.name}"}
                                   for p in sorted(assets.iterdir())]}
            fixture = root / "fixture.json"
            fixture.write_text(json.dumps({"metadata": metadata, "repository": release_repository,
                                           "anonymous": anonymous, "authenticated": authenticated}))
            (tools / "uname").write_text("#!/usr/bin/env python3\nimport os,sys\nprint(os.environ['AIV_TEST_OS'] if sys.argv[1]=='-s' else os.environ['AIV_TEST_ARCH'])\n")
            # The transport fixture only serves the selected immutable tag; a mutable
            # selector, wrong repository or unexpected request is an actual failure.
            transport = '''#!/usr/bin/env python3
import json,os,pathlib,shutil,sys
kind=pathlib.Path(sys.argv[0]).name;a=sys.argv[1:]
d=json.loads(pathlib.Path(os.environ['AIV_TEST_FIXTURE']).read_text());m=d['metadata']
with open(os.environ['AIV_TEST_LOG'],'a') as f:f.write(json.dumps([kind]+a)+'\\n')
assets=pathlib.Path(os.environ['AIV_TEST_ASSETS'])
def copy(name,destination):
 if name not in [x['name'] for x in m['assets']]:sys.exit('missing asset')
 shutil.copyfile(assets/name,destination)
if kind=='curl':
 if not d['anonymous']:sys.exit(22)
 urls=[x for x in a if x.startswith('https://')]
 if len(urls)!=1:sys.exit('expected one URL')
 url=urls[0];destination=pathlib.Path(a[a.index('--output')+1])
 if url=='https://api.github.com/repos/'+d['repository']+'/releases/tags/'+m['tag_name']:
  destination.write_text(json.dumps(m));sys.exit(0)
 for asset in m['assets']:
  if url==asset['browser_download_url']:copy(asset['name'],destination);sys.exit(0)
 sys.exit('unexpected anonymous request')
if not d['authenticated']:sys.exit('fixture has no authenticated GitHub account')
if a[:2]==['auth','status']:sys.exit(0)
if a[:1]==['api']:
 if a[1]!='repos/'+d['repository']+'/releases/tags/'+m['tag_name']:sys.exit('wrong metadata request')
 print(json.dumps(m));sys.exit(0)
if a[:2]==['release','download']:
 if a[2]!=m['tag_name'] or a[a.index('-R')+1]!=d['repository']:sys.exit('wrong download identity')
 destination=pathlib.Path(a[a.index('--dir')+1]);destination.mkdir(exist_ok=True)
 for i,arg in enumerate(a):
  if arg=='-p':copy(a[i+1],destination/a[i+1])
 sys.exit(0)
sys.exit('unexpected gh operation')
'''
            for command in ("curl", "gh"):
                (tools / command).write_text(transport)
            for tool in tools.iterdir():
                tool.chmod(0o755)
            log = root / "transport.jsonl"
            environment = {**os.environ, "PATH": str(tools) + os.pathsep + os.environ["PATH"],
                           "AIV_TEST_OS": os_name, "AIV_TEST_ARCH": arch,
                           "AIV_INSTALL_DIR": str(installed), "AIV_TEST_FIXTURE": str(fixture),
                           "AIV_TEST_LOG": str(log), "AIV_TEST_ASSETS": str(assets)}
            for key in ("AIV_TAG", "AIV_REPOSITORY"):
                environment.pop(key, None)
            if existing_release:
                (root / "verified-release").mkdir()
                (root / "verified-release" / "operator-restore-set").write_text("preserve me")
            if save_release:
                environment["AIV_RELEASE_DIR"] = str(root / "verified-release")
            else:
                environment.pop("AIV_RELEASE_DIR", None)
            if not unset_tag:
                environment["AIV_TAG"] = tag or release_tag
            if repository is not None or historical:
                environment["AIV_REPOSITORY"] = repository or HISTORICAL_REPOSITORY
            result = subprocess.run(["bash", "-c", recipe(skill)], cwd=root, env=environment,
                                    capture_output=True, text=True, timeout=20)
            calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
            return {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
                    "calls": calls, "installed": (installed / "aiv").read_bytes(), "original": original, "saved": sorted(p.name for p in (root / "verified-release").iterdir()) if (root / "verified-release").exists() else []}

    def assert_preserved(self, result):
        self.assertNotEqual(result["exit_code"], 0, result)
        self.assertEqual(result["installed"], result["original"], result)

    def test_each_standalone_recipe_installs_explicit_public_daily_without_auth(self):
        for skill in SKILLS:
            for machine in ("x86_64", "aarch64"):
                with self.subTest(skill=skill, arch=machine):
                    result = self.run_recipe(skill, arch=machine, extra=True)
                    self.assertEqual(result["exit_code"], 0, result)
                    self.assertIn("aiv " + NEW_VERSION, result["stdout"])
                    self.assertFalse(any(call[0] == "gh" for call in result["calls"]), result)

    def test_deployment_can_retain_checksummed_manifest_and_matching_vars(self):
        result = self.run_recipe(save_release=True)
        self.assertEqual(result["exit_code"], 0, result)
        self.assertEqual(result["saved"], ["SHA256SUMS", "release-images.vars.yaml", "release-manifest.json", "release-seekdb.vars.yaml"])

    def test_saved_release_directory_is_never_overwritten(self):
        result = self.run_recipe(save_release=True, existing_release=True)
        self.assert_preserved(result)
        self.assertEqual(result["saved"], ["operator-restore-set"])

    def test_manifest_and_both_vars_must_have_valid_checksums(self):
        for asset in ("release-manifest.json", "release-images.vars.yaml", "release-seekdb.vars.yaml"):
            with self.subTest(asset=asset):
                result = self.run_recipe(bad_checksum=asset, save_release=True)
                self.assert_preserved(result)
                self.assertEqual(result["saved"], [])

    def test_exact_public_stable_and_macos_archive_are_supported(self):
        result = self.run_recipe(version="0.1.0", os_name="Darwin", arch="arm64")
        self.assertEqual(result["exit_code"], 0, result)

    def test_private_product_uses_authenticated_fallback(self):
        result = self.run_recipe(anonymous=False, authenticated=True)
        self.assertEqual(result["exit_code"], 0, result)
        self.assertTrue(any(call[:2] == ["gh", "api"] for call in result["calls"]), result)

    def test_missing_explicit_version_and_mutable_selectors_preserve_binary(self):
        for changes in ({"unset_tag": True}, {"tag": "daily"}, {"tag": "latest"}, {"tag": "v0.1.0-dev.20990101"}):
            with self.subTest(changes=changes):
                result = self.run_recipe(**changes)
                self.assert_preserved(result)
                self.assertFalse(result["calls"], result)

    def test_manifest_identity_and_channel_must_match_exact_product_release(self):
        for changes in ({"source_repository": HISTORICAL_REPOSITORY},
                        {"release_tag": "v0.1.0-daily.20990102"},
                        {"product_version": "0.1.0-daily.20990102"}, {"channel": "stable"}):
            with self.subTest(changes=changes):
                self.assert_preserved(self.run_recipe(manifest_changes=changes))

    def test_draft_wrong_channel_missing_manifest_or_archive_preserves_binary(self):
        for changes in ({"draft": True}, {"prerelease": False},
                        {"missing": "release-manifest.json"}, {"missing": "aiv-linux-arm64.tar.gz"},
                        {"wrong_binary_version": True}, {"bad_checksum": True}):
            with self.subTest(changes=changes):
                self.assert_preserved(self.run_recipe(**changes))

    def test_explicit_historical_native_deliveries_keep_auth_and_platform_guards(self):
        for version in HISTORICAL_VERSIONS:
            with self.subTest(version=version):
                result = self.run_recipe(version=version, historical=True, arch="x86_64", authenticated=True)
                self.assertEqual(result["exit_code"], 0, result)
                self.assertFalse(any(call[0] == "curl" for call in result["calls"]), result)
                self.assert_preserved(self.run_recipe(version=version, historical=True, arch="x86_64"))
        self.assert_preserved(self.run_recipe(version=HISTORICAL_VERSIONS[0], historical=True, authenticated=True))

    def test_historical_manifest_must_identify_its_exact_delivery(self):
        for delivery in ({"repository": PRODUCT_REPOSITORY, "release_tag": "delivery-v" + HISTORICAL_VERSIONS[0]},
                         {"repository": HISTORICAL_REPOSITORY, "release_tag": "delivery-v0.0.1-daily.20990101"}):
            with self.subTest(delivery=delivery):
                self.assert_preserved(self.run_recipe(version=HISTORICAL_VERSIONS[0], historical=True,
                                                     arch="x86_64", authenticated=True,
                                                     manifest_changes={"delivery": delivery}))

    def test_historical_guards_reject_unapproved_tags_repository_and_extra_assets(self):
        for changes in ({"version": "0.0.1-daily.20261028"}, {"version": "0.1.0-daily.20990101"},
                        {"repository": PRODUCT_REPOSITORY}, {"extra": True}):
            with self.subTest(changes=changes):
                self.assert_preserved(self.run_recipe(historical=True, arch="x86_64", authenticated=True, **changes))


if __name__ == "__main__":
    unittest.main()
