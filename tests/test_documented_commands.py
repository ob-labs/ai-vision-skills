"""Run the public install examples with local download fixtures."""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / 'skills/aivision-deploy/reference/all-in-one.md'
DAILY = 'v0.6.0-daily.20261123.2'
RELEASE_URL = f'https://github.com/antgroup/ai-vision/releases/download/{DAILY}'
ARCHIVE = 'aiv-all-in-one-linux-arm64.tar.zst'
INSTALLER = b'import json, sys\nfrom pathlib import Path\nPath("installer.json").write_text(json.dumps(sys.argv[1:]))\n'
IMAGE = b'All-in-One image archive fixture\n'
PROXIES = ('https://ghfast.top', 'https://gh-proxy.org')
SHELL_BLOCK = re.compile(r'^```(?:bash|sh)\n(.*?)^```$', re.MULTILINE | re.DOTALL)


def example(source, *, heading=None):
    text = source.read_text(encoding='utf-8')
    if heading:
        section = text.split(f'\n### {heading}\n', 1)[1]
        text = re.split(r'\n#{1,3} ', section, maxsplit=1)[0]
    blocks = SHELL_BLOCK.findall(text)
    if not heading:
        blocks = [block for block in blocks if 'npx skills add ' in block and '--list' in block]
    if len(blocks) != 1:
        raise ValueError(f'Expected one shell example in {source.name} {heading or ""}')
    return blocks[0]


def checksums(name, data):
    return f'{hashlib.sha256(data).hexdigest()}  {name}\n'.encode()


CURL = '''#!/usr/bin/env python3
import json, sys
from pathlib import Path

args = sys.argv[1:]
url = args[-1]
with Path('downloads.jsonl').open('a') as log:
    log.write(json.dumps(url) + '\\n')
assert args[0] == '-q' and '--fail' in args and '--location' in args
for option in ('--proto', '--proto-redir'):
    assert args[args.index(option) + 1] == '=https'
assert not any('authorization:' in arg.lower() for arg in args)
if not url.startswith('https://github.com/'):
    assert args[args.index('--continue-at') + 1] == '-'
assets = json.loads(Path('downloads.json').read_text())
if url not in assets:
    sys.exit(22)
Path(args[args.index('--output') + 1]).write_bytes(bytes.fromhex(assets[url]))
'''


class DocumentedCommandsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='aivision-doc-command-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.tools = self.root / 'bin'
        self.tools.mkdir()

    def tool(self, name, content):
        path = self.tools / name
        path.write_text(content, encoding='utf-8')
        path.chmod(0o755)

    def run_example(self, command, directory, tag=DAILY):
        env = {**os.environ, 'PATH': str(self.tools) + os.pathsep + os.environ['PATH']}
        env.pop('release_tag', None)
        if tag is not None:
            env['release_tag'] = tag
        return subprocess.run(['sh', '-c', command], cwd=directory, env=env,
                              capture_output=True, text=True, timeout=15)

    def test_readmes_use_the_public_catalog_for_discovery_and_installation(self):
        self.tool('npx', '#!/bin/sh\nprintf "%s\\n" "$*" >> npx.log\n')
        for name in ('README.md', 'README.zh-CN.md', 'README.ja-JP.md'):
            with self.subTest(readme=name):
                project = self.root / name
                project.mkdir()
                result = self.run_example(example(ROOT / name), project)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((project / 'npx.log').read_text().splitlines(), [
                    'skills add ob-labs/ai-vision-skills --list',
                    'skills add ob-labs/ai-vision-skills --skill aivision-deploy --agent codex',
                ])

    def run_download_example(self, command, downloads, *, sums=None, tag=DAILY):
        self.tool('curl', CURL)
        if sys.platform == 'darwin':
            # macOS ships sha256sum with different option names from GNU coreutils.
            self.tool('sha256sum', '#!/bin/sh\nexec shasum -a 256 "$@"\n')
        with tempfile.TemporaryDirectory(dir=self.root) as temporary:
            project = Path(temporary)
            (project / 'downloads.json').write_text(json.dumps({url: data.hex() for url, data in downloads.items()}))
            if sums is not None:
                (project / 'SHA256SUMS').write_bytes(sums)
            result = self.run_example(command, project, tag=tag)
            log = project / 'downloads.jsonl'
            requests = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
            invocation = project / 'installer.json'
            return result, requests, json.loads(invocation.read_text()) if invocation.exists() else None

    def test_official_recipe_runs_only_the_verified_installer(self):
        installer_url, sums_url = (f'{RELEASE_URL}/{name}' for name in ('install-all-in-one.py', 'SHA256SUMS'))
        command = example(GUIDE, heading='Run the installer directly')
        valid_sums = checksums('install-all-in-one.py', INSTALLER)
        downloads = {installer_url: INSTALLER, sums_url: valid_sums}
        result, requests, invocation = self.run_download_example(command, downloads)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(requests, [installer_url, sums_url])
        self.assertEqual(invocation, ['--tag', DAILY])

        for name, assets in {
            'installer download failed': {sums_url: valid_sums},
            'checksum download failed': {installer_url: INSTALLER},
            'installer missing from checksum list': {**downloads, sums_url: checksums('other.py', INSTALLER)},
            'installer bytes differ': {**downloads, installer_url: INSTALLER + b'# modified\n'},
        }.items():
            with self.subTest(case=name):
                result, _, invocation = self.run_download_example(command, assets)
                self.assertNotEqual(result.returncode, 0)
                self.assertIsNone(invocation)

    def test_opt_in_proxy_recipe_verifies_the_archive_against_the_local_official_checksum(self):
        command = example(GUIDE, heading='Speed up a slow download')
        valid_sums = checksums(ARCHIVE, IMAGE)
        for proxy in PROXIES:
            recipe = command if proxy == PROXIES[0] else command.replace(f'proxy={PROXIES[0]}\n', f'proxy={proxy}/\n', 1)
            archive_url = f'{proxy}/{RELEASE_URL}/{ARCHIVE}'
            with self.subTest(proxy=proxy):
                result, requests, invocation = self.run_download_example(recipe, {archive_url: IMAGE}, sums=valid_sums)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(requests, [archive_url])
                self.assertIsNone(invocation)

        archive_url = f'{PROXIES[0]}/{RELEASE_URL}/{ARCHIVE}'
        for name, assets, sums in (
            ('archive download failed', {}, valid_sums),
            ('missing checksum list', {archive_url: IMAGE}, None),
            ('archive missing from checksum list', {archive_url: IMAGE}, checksums('other.tar.zst', IMAGE)),
            ('archive bytes differ', {archive_url: b'modified'}, valid_sums),
        ):
            with self.subTest(case=name):
                result, requests, invocation = self.run_download_example(command, assets, sums=sums)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(requests, [archive_url])
                self.assertIsNone(invocation)

    def test_download_recipes_require_an_exact_daily_tag(self):
        for heading in ('Run the installer directly', 'Speed up a slow download'):
            for tag in (None, 'daily'):
                with self.subTest(heading=heading, tag=tag):
                    result, requests, invocation = self.run_download_example(example(GUIDE, heading=heading), {}, tag=tag)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(requests, [])
                    self.assertIsNone(invocation)
