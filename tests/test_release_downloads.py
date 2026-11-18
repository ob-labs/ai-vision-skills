"""Exercise each public CLI installer against published-release HTTP fixtures."""
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
SKILLS = ('aivision-deploy', 'aivision-quickstart', 'aivision-trace', 'aivision-metric')
REPOSITORY = 'antgroup/ai-vision'
STABLE = 'v0.6.0'
DAILY = 'v0.6.0-daily.20261118.2'
ORIGINAL = b'existing CLI\n'
ROLES = {'aivision-be': 'backend', 'aivision-fe': 'frontend', 'agentlens': 'diagnosis',
         'antcollector-gw': 'ingest-gateway', 'signoz-ob': 'data-backend'}


def digest(value):
    return hashlib.sha256(value).hexdigest()


def cli_archive(platform, version):
    binary = f"#!/bin/sh\nprintf '%s\\n' 'aiv {version}'\n".encode()
    output = io.BytesIO()
    if platform == 'windows-x64':
        with zipfile.ZipFile(output, 'w') as archive:
            entry = zipfile.ZipInfo('aiv.exe')
            entry.create_system = 3
            entry.external_attr = (stat.S_IFREG | 0o755) << 16
            archive.writestr(entry, binary)
    else:
        with tarfile.open(fileobj=output, mode='w:gz') as archive:
            entry = tarfile.TarInfo('aiv')
            entry.mode = 0o755
            entry.size = len(binary)
            archive.addfile(entry, io.BytesIO(binary))
    return output.getvalue()


def published(tag, *platforms, draft=False, unpublished=False, wrong_version=False,
              invalid_manifest=None, missing=(), bad_checksum=False):
    is_daily = '-daily.' in tag
    version = tag.removeprefix('v')
    assets = {}
    for platform in platforms:
        suffix = 'zip' if platform == 'windows-x64' else 'tar.gz'
        assets[f'aiv-{platform}.{suffix}'] = cli_archive(platform, '9.9.9' if wrong_version else version)
    manifest = {'source_repository': REPOSITORY, 'source_sha': 'a' * 40,
                'build_id': '44371617206.1', 'release_tag': tag, 'product_version': version,
                'channel': 'daily' if is_daily else 'stable',
                'images': {key: f'ghcr.io/{REPOSITORY}/{role}@sha256:' + 'b' * 64 for key, role in ROLES.items()}}
    manifest.update(invalid_manifest or {})
    assets.update({'release-manifest.json': json.dumps(manifest).encode(),
                   'release-images.vars.yaml': b'OB_BACKEND: "oceanbase"\n',
                   'release-seekdb.vars.yaml': b'OB_BACKEND: "seekdb"\n'})
    for name in missing:
        assets.pop(name)
    assets['SHA256SUMS'] = ''.join(f"{'0' * 64 if bad_checksum else digest(data)}  {name}\n"
                                  for name, data in assets.items()).encode()
    return ({'id': tag, 'tag_name': tag, 'draft': draft, 'prerelease': is_daily or '-rc.' in tag,
             'published_at': None if unpublished else '2026-11-19T00:00:00Z',
             'assets': [{'id': name, 'name': name, 'state': 'uploaded', 'size': len(data),
                         'digest': 'sha256:' + digest(data)} for name, data in assets.items()]}, assets)


CURL_FIXTURE = '''#!/usr/bin/env python3
import json, os, pathlib, sys
from urllib.parse import parse_qs, urlsplit
args = sys.argv[1:]
root = pathlib.Path(os.environ['AIV_TEST_ROOT'])
url = urlsplit(next(arg for arg in args if arg.startswith('https://')))
urls = root/'urls.jsonl'
queries = [json.loads(line) for line in urls.read_text().splitlines()] if urls.exists() else []
assert not any('authorization:' in arg.lower() for arg in args)
with urls.open('a') as log:
    log.write(json.dumps(url.geturl()) + '\\n')
metadata = json.loads((root/'metadata.json').read_text())
if url.netloc == 'api.github.com':
    assert url.path.startswith('/repos/antgroup/ai-vision/releases')
    if url.path.endswith('/releases'):
        page = int(parse_qs(url.query)['page'][0])
        data = json.dumps(metadata['pages'][page-1]).encode()
    else:
        assert '/releases/tags/' in url.path
        tag = url.path.rsplit('/', 1)[-1]
        release = metadata['exact'][tag]
        if tag == metadata['changed_readback'] and url.geturl() in queries:
            release['assets'][0]['digest'] = 'sha256:' + '0' * 64
        data = json.dumps(release).encode()
else:
    assert url.netloc == 'github.com'
    prefix = '/antgroup/ai-vision/releases/download/'
    assert url.path.startswith(prefix)
    tag, name = url.path.removeprefix(prefix).split('/')
    data = (root/'assets'/tag/name).read_bytes()
if '-o' in args:
    pathlib.Path(args[args.index('-o')+1]).write_bytes(data)
else:
    sys.stdout.buffer.write(data)
'''


class PublicDownloadTests(unittest.TestCase):
    def run_recipe(self, releases, *, skill=SKILLS[0], mode='--resolve', tag='', channel='',
                   system='Linux', architecture='x86_64', hardware='0', changed_readback=False,
                   changed_download=None, repository='', powershell=None):
        with tempfile.TemporaryDirectory(prefix='aiv-public-release-') as directory:
            root = Path(directory)
            tools, destination = root / 'tools', root / 'install'
            tools.mkdir()
            destination.mkdir()
            binary = destination / ('aiv.exe' if powershell else 'aiv')
            binary.write_bytes(ORIGINAL)
            exact = {release['tag_name']: release for release, _ in releases}
            pages = [[release for release, _ in releases[index:index + 100]]
                     for index in range(0, len(releases), 100)] or [[]]
            if len(releases) and len(releases) % 100 == 0:
                pages.append([])
            (root / 'metadata.json').write_text(json.dumps({'pages': pages, 'exact': exact,
                                                           'changed_readback': tag if changed_readback else None}))
            for release, assets in releases:
                source = root / 'assets' / release['tag_name']
                source.mkdir(parents=True)
                for name, value in assets.items():
                    (source / name).write_bytes(value)
            if changed_download:
                (root / 'assets' / tag / changed_download).write_bytes(b'tampered bytes\n')
            (tools / 'uname').write_text('#!/bin/sh\ncase "$1" in -s) echo "$AIV_TEST_OS";; -m) echo "$AIV_TEST_ARCH";; esac\n')
            (tools / 'sysctl').write_text('#!/bin/sh\nprintf "%s\\n" "$AIV_TEST_HARDWARE"\n')
            (tools / 'curl').write_text(CURL_FIXTURE)
            (tools / 'gh').write_text('#!/bin/sh\nexit 99\n')
            for tool in tools.iterdir():
                tool.chmod(0o755)
            env = {key: value for key, value in os.environ.items()
                   if not key.startswith(('AIV_', 'GH_TOKEN', 'GITHUB_TOKEN'))}
            env.update(PATH=str(tools) + os.pathsep + env['PATH'], AIV_TAG=tag, AIV_CHANNEL=channel,
                       AIV_REPOSITORY=repository, AIV_INSTALL_DIR=str(destination),
                       AIV_TEST_ROOT=str(root), AIV_TEST_OS=system, AIV_TEST_ARCH=architecture,
                       AIV_TEST_HARDWARE=hardware)
            scripts = ROOT / 'skills' / skill / 'scripts'
            if powershell:
                hardware_probe = '[System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()'
                helper = root / 'install-cli.ps1'
                helper.write_text((scripts / 'install-cli.ps1').read_text().replace(hardware_probe, "'X64'"))
                for jq_file in scripts.glob('*.jq'):
                    shutil.copyfile(jq_file, root / jq_file.name)
                command = [powershell, '-NoProfile', '-NonInteractive', '-File', str(helper),
                           '-Mode', 'Install' if mode == '--install' else 'Resolve']
            else:
                command = ['sh', str(scripts / 'install-cli.sh'), mode]
            result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, timeout=25)
            calls = root / 'urls.jsonl'
            urls = [json.loads(line) for line in calls.read_text().splitlines()] if calls.exists() else []
            return result, binary.read_bytes(), urls

    def test_independent_skill_helpers_match(self):
        for name in ('discover-cli.jq', 'verify-release-manifest.jq', 'install-cli.sh', 'install-cli.ps1'):
            self.assertEqual(len({(ROOT / 'skills' / skill / 'scripts' / name).read_bytes() for skill in SKILLS}), 1)

    def test_public_daily_install_needs_no_token_or_github_cli(self):
        for skill in SKILLS:
            with self.subTest(skill=skill):
                result, binary, urls = self.run_recipe([published(DAILY, 'linux-x64')], skill=skill,
                                                        mode='--install', tag=DAILY)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(DAILY[1:].encode(), binary)
                self.assertTrue(any(f'/releases/download/{DAILY}/aiv-linux-x64.tar.gz' in url for url in urls))

    def test_stable_default_and_numeric_daily_revisions_across_pages(self):
        releases = [published(f'v0.5.{index}', 'linux-x64') for index in range(98)]
        releases.extend([published(DAILY, 'linux-x64'), published(STABLE, 'linux-x64'),
                         published(DAILY.rsplit('.', 1)[0] + '.10', 'linux-x64')])
        for channel, expected in (('', STABLE), ('daily', DAILY.rsplit('.', 1)[0] + '.10')):
            with self.subTest(channel=channel):
                result, binary, urls = self.run_recipe(releases, channel=channel)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)['tag'], expected)
                self.assertEqual(binary, ORIGINAL)
                self.assertTrue(any('page=2' in url for url in urls))
                self.assertFalse(any(url.endswith('.tar.gz') for url in urls))

    def test_posix_platforms_and_rosetta_archive(self):
        release = published(STABLE, 'linux-x64', 'linux-arm64', 'darwin-x64', 'darwin-arm64')
        platforms = [('Linux', 'aarch64', '0', 'linux-arm64'), ('Darwin', 'arm64', '0', 'darwin-arm64'),
                     ('Darwin', 'x86_64', '1', 'darwin-arm64'), ('Darwin', 'x86_64', '0', 'darwin-x64')]
        for system, architecture, hardware, expected in platforms:
            with self.subTest(system=system, architecture=architecture, hardware=hardware):
                result, _, _ = self.run_recipe([release], system=system, architecture=architecture, hardware=hardware)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)['cli_platform'], expected)

    def test_drafts_missing_assets_and_unpublished_exact_versions_do_not_install(self):
        fixtures = [published(DAILY, 'linux-x64', draft=True), published(DAILY, 'linux-x64', unpublished=True),
                    published(DAILY, 'linux-x64', missing=('release-manifest.json',)),
                    published(DAILY, 'linux-arm64')]
        for fixture in fixtures:
            with self.subTest(fixture=fixture[0]):
                result, binary, urls = self.run_recipe([fixture], tag=DAILY, mode='--install')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(binary, ORIGINAL)
                self.assertFalse(any('/download/' in url for url in urls))

    def test_empty_public_release_catalog_preserves_the_existing_cli(self):
        for channel in ('stable', 'daily'):
            with self.subTest(channel=channel):
                result, binary, urls = self.run_recipe([], channel=channel)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f'No compatible published {channel} CLI', result.stderr)
                self.assertEqual(binary, ORIGINAL)
                self.assertEqual(urls, [f'https://api.github.com/repos/{REPOSITORY}/releases?per_page=100&page=1'])

    def test_aliases_rc_and_retired_repositories_are_rejected(self):
        for tag in ('', 'daily', 'v0.6.0-rc.1', 'delivery-v0.1.0-daily.20261108', '*'):
            with self.subTest(tag=tag):
                result, binary, urls = self.run_recipe([published(STABLE, 'linux-x64')], tag=tag, mode='--install')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(binary, ORIGINAL)
                self.assertFalse(any('/download/' in url for url in urls))
        result, binary, urls = self.run_recipe([], repository='ob-labs/ai-vision-ob')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(binary, ORIGINAL)
        self.assertEqual(urls, [])

    def test_metadata_manifest_and_binary_integrity_fail_closed(self):
        cases = [({'wrong_version': True}, {}), ({'bad_checksum': True}, {}),
                 ({'invalid_manifest': {'source_repository': 'elsewhere/product'}}, {}),
                 ({'invalid_manifest': {'product_version': '9.9.9'}}, {}),
                 ({'invalid_manifest': {'images': {'signoz-ob': 'unexpected:daily'}}}, {}),
                 ({}, {'changed_readback': True}), ({}, {'changed_download': 'SHA256SUMS'}),
                 ({}, {'changed_download': 'release-manifest.json'}),
                 ({}, {'changed_download': 'aiv-linux-x64.tar.gz'})]
        for fixture, runtime in cases:
            with self.subTest(fixture=fixture, runtime=runtime):
                result, binary, _ = self.run_recipe([published(DAILY, 'linux-x64', **fixture)], mode='--install', tag=DAILY, **runtime)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(binary, ORIGINAL)

    @unittest.skipUnless(os.name == 'posix' and shutil.which('pwsh'), 'PowerShell fixture needs pwsh on POSIX')
    def test_powershell_uses_public_manifest_and_exact_zip(self):
        powershell = shutil.which('pwsh')
        release = published(STABLE, 'windows-x64')
        result, binary, _ = self.run_recipe([release], mode='--install', tag=STABLE, powershell=powershell)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(STABLE[1:].encode(), binary)
        result, binary, _ = self.run_recipe([release], mode='--install', tag=STABLE, powershell=powershell,
                                             changed_download='aiv-windows-x64.zip')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(binary, ORIGINAL)


if __name__ == '__main__':
    unittest.main()
