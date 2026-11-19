# AI Vision Skills Development Guidelines

This repository is the canonical source for maintained AI Vision Skills. Read the relevant `skills/<name>/SKILL.md` and bundled references before editing.

- Keep Skill names and `skills/<name>/SKILL.md` discovery paths stable. Migrate complete directories, including scripts, requirements, agent metadata, and tests.
- Each Skill must work when installed independently. Keep execution-critical resources inside its own directory; cross-Skill links use the canonical repository URL.
- Use official product distribution and bundled resources for normal user workflows. Preserve actual product versions, source identities, image digests, and deployment state.
- Product/CLI source, deployment assets, and hook/plugin implementation remain product-owned. Use `antgroup/ai-vision` Releases and official product image references. Maintain the Skills source and catalog CI here.
- Repository access, Release download, image pulls, platform account login, SpaceKeys, and model credentials are separate operations. Never embed real credentials.
- Security scanning stays in the team's existing offline/manual process. Add no scanner CI jobs or mandatory scan reports/SBOMs.
- Write engineering documentation and PR text in English. Preserve explicitly localized files.
- Run catalog checks, relevant script tests, and upstream Skills discovery/installation checks. Static installation evidence does not establish live platform or model behavior.
- Inspect the final diff and `git status`; run `git diff --check`. Do not include temporary downloads, logs, credentials, build outputs, or copied product history.
- Remote commits, pushes, repository permissions, publication, and visibility changes require user authorization. Apply the user's current explicit publication scope; repository setup alone does not authorize unrelated publication or access grants.
