"""Exercise the real independently bundled shell download recipes with fixtures.

The fake GitHub service supplies archive bytes and records requested assets.
The recipes use the real shell, tar, checksum and atomic install operations.
No HOME/CODEX_HOME change, real credentials, network, platform or model is used.
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
NEW_VERSION = "0.0.1-daily.20261029"
OLD_VERSION = "0.0.1-daily.20261028.2"
SKILLS = ("aivision-deploy", "aivision-quickstart", "aivision-trace", "aivision-metric")


def recipe(skill):
    text = (ROOT / "skills" / skill / "reference/install-cli.md").read_text()
    return next(block for block in re.findall(r"```bash\n(.*?)\n```", text, re.S)
                if "AIV_TAG=" in block and "AIV_REPOSITORY=" in block)


class DownloadRecipeTests(unittest.TestCase):
    def run_recipe(self, skill="aivision-quickstart", *, arch="aarch64", os_name="Linux",
                   version=NEW_VERSION, explicit=False, missing=None, extra=False,
                   draft=False, wrong_binary_version=False, bad_checksum=False):
        with tempfile.TemporaryDirectory(prefix="aiv-catalog-download-") as temporary:
            root = Path(temporary)
            tools, assets, installed = root / "tools", root / "assets", root / "install"
            tools.mkdir(); assets.mkdir(); installed.mkdir()
            original = b"existing installed binary\n"
            (installed / "aiv").write_bytes(original)
            tag = "delivery-v" + version
            cli_arches = ["x64"] if version == OLD_VERSION else ["x64", "arm64"]
            for target in cli_arches:
                binary_version = "0.0.1" if wrong_binary_version else version
                payload = f"#!/bin/sh\nprintf '%s\\n' 'aiv {binary_version}'\n".encode()
                with tarfile.open(assets / f"aiv-linux-{target}.tar.gz", "w:gz") as archive:
                    member = tarfile.TarInfo("aiv"); member.mode = 0o755; member.size = len(payload)
                    archive.addfile(member, io.BytesIO(payload))
            image_platforms = ["linux/amd64"] if version == OLD_VERSION else ["linux/amd64", "linux/arm64"]
            (assets / "release-manifest.json").write_text(json.dumps({
                "product_version": version, "channel": "daily", "image_platforms": image_platforms,
                "cli_platforms": ["linux-" + x for x in cli_arches],
            }))
            for name in ["install-aiv.sh", "release-images.vars.yaml", "release-seekdb.vars.yaml"]:
                (assets / name).write_text("fixture\n")
            (assets / "SHA256SUMS").write_text("".join(
                f"{('0' * 64) if bad_checksum else hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n"
                for p in sorted(assets.iterdir()) if p.name != "SHA256SUMS"))
            if missing:
                (assets / missing).unlink()
            if extra:
                (assets / "unexpected-source.tar.gz").write_bytes(b"not an approved asset")
            fixture = root / "fixture.json"
            fixture.write_text(json.dumps({"tag": tag, "isDraft": draft, "isPrerelease": True,
                                           "assets": sorted(p.name for p in assets.iterdir())}))
            (tools / "uname").write_text("#!/usr/bin/env python3\nimport os,sys\nprint(os.environ['AIV_TEST_OS'] if sys.argv[1]=='-s' else os.environ['AIV_TEST_ARCH'])\n")
            (tools / "gh").write_text('''#!/usr/bin/env python3
import json,os,pathlib,shutil,sys
a=sys.argv[1:];d=json.loads(pathlib.Path(os.environ['AIV_TEST_FIXTURE']).read_text())
with open(os.environ['AIV_TEST_LOG'],'a') as f:f.write(json.dumps(a)+'\\n')
if a[:2]==['auth','status']:sys.exit(0)
if a[:2]==['release','view']:
 if a[2]!=d['tag']:sys.exit('requested Release is not published')
 if a[a.index('--json')+1]=='assets':print('\\n'.join(d['assets']))
 elif not d['isDraft'] and d['isPrerelease']:print(d['tag'])
 sys.exit(0)
if a[:2]==['release','download']:
 if a[2]!=d['tag']:sys.exit('wrong download version')
 destination=pathlib.Path(a[a.index('--dir')+1]);destination.mkdir(exist_ok=True)
 for i,arg in enumerate(a):
  if arg=='-p':
   name=a[i+1]
   if name not in d['assets']:sys.exit('missing asset')
   shutil.copyfile(pathlib.Path(os.environ['AIV_TEST_ASSETS'])/name,destination/name)
 sys.exit(0)
sys.exit('unexpected gh operation')
''')
            for tool in tools.iterdir():
                tool.chmod(0o755)
            log = root / "gh.jsonl"
            environment = {**os.environ, "PATH": str(tools) + os.pathsep + os.environ["PATH"],
                           "AIV_TEST_OS": os_name, "AIV_TEST_ARCH": arch,
                           "AIV_INSTALL_DIR": str(installed), "AIV_TEST_FIXTURE": str(fixture),
                           "AIV_TEST_LOG": str(log), "AIV_TEST_ASSETS": str(assets)}
            if explicit:
                environment["AIV_TAG"] = tag
            else:
                environment.pop("AIV_TAG", None)
            result = subprocess.run(["bash", "-c", recipe(skill)], cwd=root, env=environment,
                                    capture_output=True, text=True, timeout=20)
            calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
            return {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
                    "calls": calls, "installed": (installed / "aiv").read_bytes(),
                    "original": original}

    def test_default_linux_arm64(self):
        result = self.run_recipe()
        self.assertEqual(result["exit_code"], 0, result)
        self.assertIn("aiv " + NEW_VERSION, result["stdout"])
        downloads = [call for call in result["calls"] if call[:2] == ["release", "download"]]
        self.assertTrue(downloads)
        self.assertIn("aiv-linux-arm64.tar.gz", downloads[0])

    def test_each_independent_skill_selects_both_linux_platforms(self):
        for skill in SKILLS:
            for machine, asset in [("x86_64", "aiv-linux-x64.tar.gz"), ("aarch64", "aiv-linux-arm64.tar.gz")]:
                with self.subTest(skill=skill, arch=machine):
                    result = self.run_recipe(skill, arch=machine)
                    self.assertEqual(result["exit_code"], 0, result)
                    self.assertNotEqual(result["installed"], result["original"])
                    downloads = [call for call in result["calls"] if call[:2] == ["release", "download"]]
                    self.assertIn(asset, downloads[0])
                    self.assertEqual(downloads[0][2], "delivery-v" + NEW_VERSION)

    def test_explicit_old_corrected_x64_delivery_still_installs(self):
        result = self.run_recipe(arch="x86_64", version=OLD_VERSION, explicit=True)
        self.assertEqual(result["exit_code"], 0, result)
        self.assertIn("aiv " + OLD_VERSION, result["stdout"])

    def test_explicit_old_corrected_delivery_rejects_arm(self):
        result = self.run_recipe(version=OLD_VERSION, explicit=True)
        self.assertNotEqual(result["exit_code"], 0)
        self.assertEqual(result["installed"], result["original"])
        self.assertFalse(result["calls"])

    def test_original_source_bearing_delivery_is_rejected(self):
        result = self.run_recipe(version="0.0.1-daily.20261028", explicit=True)
        self.assertNotEqual(result["exit_code"], 0)
        self.assertEqual(result["installed"], result["original"])
        self.assertFalse(result["calls"])

    def test_missing_arm_or_extra_assets_preserve_installed_binary(self):
        for changes in [{"missing": "aiv-linux-arm64.tar.gz", "arch": "x86_64"}, {"extra": True}]:
            with self.subTest(changes=changes):
                result = self.run_recipe(**changes)
                self.assertNotEqual(result["exit_code"], 0)
                self.assertEqual(result["installed"], result["original"])
                self.assertFalse(any(x[:2] == ["release", "download"] for x in result["calls"]))

    def test_unpublished_wrong_binary_and_bad_checksum_preserve_installed_binary(self):
        for changes in [{"draft": True}, {"wrong_binary_version": True}, {"bad_checksum": True}]:
            with self.subTest(changes=changes):
                result = self.run_recipe(**changes)
                self.assertNotEqual(result["exit_code"], 0)
                self.assertEqual(result["installed"], result["original"])

    def test_new_daily_does_not_advertise_a_darwin_binary(self):
        result = self.run_recipe(os_name="Darwin", arch="arm64")
        self.assertNotEqual(result["exit_code"], 0)
        self.assertEqual(result["installed"], result["original"])


if __name__ == "__main__":
    unittest.main()
