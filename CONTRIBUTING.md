# Contributing

This repository owns the maintained AI Vision Skills and their bundled execution resources. Product implementation and canonical deployment assets remain with the product. Read [AGENTS.md](AGENTS.md) and the Skill you plan to edit.

## Change scope

Keep `skills/<name>/SKILL.md` names stable and provide concise `name` and `description` frontmatter. Use references for substantial conditional details. An independently installed Skill must contain its execution-critical resources; cross-Skill links point to this repository. Avoid a private product checkout as a user prerequisite.

Preserve supported deployment lifecycle, identity, authentication, telemetry, and compatibility constraints. A Skill edit must not invent missing CLI capabilities, Release assets, runtime evidence, or extra user authorizations. Keep credentials in private local configuration and out of commits, screenshots, fixtures, and command output.

When adding a Skill, update `README.md`, `README.zh-CN.md`, `README.ja-JP.md`, and `skills/README.md`. Keep the tests and dependencies needed to use and verify each bundle. Install Skills from this Git catalog. Use `antgroup/ai-vision` for product images and Release assets. Test product download selection with release metadata fixtures and keep executable recipes independent of any one version. See [distribution ownership](docs/distribution.md).

## Checks

Run the same checks as CI on a POSIX host with Python 3.11 or later, Node.js 22.20 or later, `jq`, and PowerShell (`pwsh`). Use a Python virtual environment for the Quickstart dependencies. The installation check runs the pinned upstream CLI `skills@1.7.4`.

```bash
python3 scripts/check_catalog.py
python3 -m unittest discover -s tests -v
python3 -m pip install -r skills/aivision-quickstart/scripts/requirements.txt
python3 -m unittest discover -s skills/aivision-quickstart/tests -v
python3 scripts/check_installation.py
git diff --check
```

The installation check discovers every Skill and copies each one into a separate disposable Codex project. The catalog check validates bundled Markdown section links. The installer tests exercise release discovery, binary verification, and the documented install commands with local fixtures. The PowerShell installer test uses a POSIX test host, so native Windows qualification requires a separate run. Quickstart exercises its SDK against local HTTP fixtures. State the results of any live deployment, platform access, or model-provider checks separately.

The `catalog` check runs on pull requests and pushes to `main` using a hosted Ubuntu runner and a read-only checkout token. It is required for merging to `main` and uses the catalog checkout and public Python and npm packages.

The [public installation workflow](.github/workflows/public-install.yml) runs after pushes to `main`, on a schedule, and on demand. It lists the public catalog and installs the deployment and Quickstart Skills into clean Codex projects using the current npm CLI without GitHub credentials. It compares the results with the `main` commit being checked. Check this workflow separately for problems with public GitHub access or upstream CLI compatibility.

The [live All-in-One Quickstart workflow](.github/workflows/live-quickstart.yml) runs weekly and on demand. It verifies and installs the latest published Daily that includes Personal Edition, registers a disposable user in Chromium, and reads back the built-in synthetic Session, Trace, and tool span in that user's personal Space. The run uses no model credentials and cleans up its temporary deployment.

For a local rehearsal, use a Linux Docker daemon with the classic image store, Node.js, and the pinned Playwright browser tools from the workflow. The released installer compares the loaded image ID with the published configuration digest, so the workflow selects the classic image store on its disposable runner. Run `python3 -B scripts/check_live_quickstart.py` with `NODE_PATH` and `PLAYWRIGHT_BROWSERS_PATH` set as in the workflow. The optional `--cache-dir` reuses an archive from the official Release after checking its SHA-256.

Security scans are handled by the team's existing offline/manual process. Do not add security scanner CI, scan-result gates, or mandatory SBOM/report generation as part of catalog maintenance.

## Review and publication

Explain the problem, changed behavior, exact validation, and compatibility limits in a pull request. Review the full diff and filenames before publication. Changes to remote contents, permissions, Release assets, or visibility require authorization from the user or responsible maintainer. Do not copy product Git history or publish private trial materials by changing visibility.
