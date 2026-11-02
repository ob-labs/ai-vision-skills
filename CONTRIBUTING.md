# Contributing

This repository owns the maintained AI Vision Skills and their bundled execution resources. Product implementation and canonical deployment assets remain with the product. Read [AGENTS.md](AGENTS.md) and the Skill you plan to edit.

## Change scope

Keep `skills/<name>/SKILL.md` names stable and provide concise `name` and `description` frontmatter. Use references for substantial conditional details. An independently installed Skill must contain its execution-critical resources; cross-Skill links point to this repository. Avoid a private product checkout as a user prerequisite.

Preserve supported deployment lifecycle, identity, authentication, telemetry, and compatibility constraints. A Skill edit must not invent missing CLI capabilities, Release assets, runtime evidence, or extra user authorizations. Keep credentials in private local configuration and out of commits, screenshots, fixtures, and command output.

When adding a Skill, update both catalog indexes. Preserve relevant tests and bundled dependencies. Product versioning is independent of catalog tags; reserve `skills-v<catalog-version>` for catalog-only versions. Restricted Daily delivery tags use immutable `delivery-v<product-version>` prereleases and explicit matching assets. The `0.1.0-daily.20261101` trial target has a seven-asset allowlist in [distribution ownership](docs/distribution.md). Historical tests retain the older AMD64-only six-asset format without promising old downloads. New architecture support uses a new accepted version without moving an earlier immutable tag; authorized retirement preserves private evidence and is not an automatic publication step.

## Checks

Use Python 3.11 or later and Node.js 22.20 or later. The pinned upstream CLI used by CI is `skills@1.7.4`.

```bash
python3 scripts/check_catalog.py
python3 -m unittest discover -s tests  # includes actual shell download recipes for both Linux architectures
python3 -m unittest discover -s skills/aivision-quickstart/tests
npx --yes skills@1.7.4 add . --list
git diff --check
```

Test independent installation in a disposable directory, with an explicit agent, before changing the original repository's migration pointers. Do not install validation copies into a user's actual global Skill directories. Run changed scripts against meaningful fixtures and explain untested live services or provider calls.

Security scans are handled by the team's existing offline/manual process. Do not add security scanner CI, scan-result gates, or mandatory SBOM/report generation as part of catalog maintenance.

## Review and publication

Explain the problem, changed behavior, exact validation, and compatibility limits in a pull request. Review the full diff and filenames before publication. Changes to remote contents, permissions, Release assets, or visibility require authorization from the user or responsible maintainer. Do not copy product Git history or publish private trial materials by changing visibility.
