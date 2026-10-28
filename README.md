# AI Vision Skills

The maintained AI Vision Skill catalog for deploying the platform, trying an Agent, inspecting traces, and querying usage. This repository is the canonical source for these Skills and the restricted-trial Daily delivery channel. Product source, CLI builds, canonical deployment assets, and telemetry plugin implementation remain in the product repository.

## Install

The repository is currently private. Use an authorized Git credential, GitHub CLI session, or SSH connection to access it. Repository access, CLI downloads, image pulls, and AI Vision credentials are separate operations.

```bash
# Discover the catalog without installing
npx skills add ob-labs/ai-vision-skills --list

# Install one Skill into the current project
npx skills add ob-labs/ai-vision-skills --skill aivision-deploy

# Install Quickstart globally for your selected agent
npx skills add ob-labs/ai-vision-skills --skill aivision-quickstart --global
```

The upstream Skills CLI requires Node.js 22.20 or later. Validation uses `skills@1.7.4`; an existing compatible CLI may be used interactively. Select an agent during installation or pass `--agent codex` or `--agent claude-code` explicitly. Installing a Skill installs instructions and bundled resources; it does not deploy AI Vision, connect an Agent, or run a model.

| Skill | Use |
|---|---|
| [aivision-deploy](skills/aivision-deploy/SKILL.md) | Deploy, verify, and upgrade the platform while retaining deployment identity and telemetry |
| [aivision-quickstart](skills/aivision-quickstart/SKILL.md) | Reuse an existing platform, configure a model, and exercise real requests with a test Agent |
| [aivision-trace](skills/aivision-trace/SKILL.md) | Query and inspect traces and export selected data |
| [aivision-metric](skills/aivision-metric/SKILL.md) | Query latency, errors, usage, and available cost metrics |

Copy the complete Skill directory for manual installation: `SKILL.md`, references, scripts, requirements, and agent metadata belong together. Each Skill can be installed independently. See the [catalog guide](skills/README.md) for prerequisites and workflow selection.

## Existing installations

If you previously installed from `ob-labs/ai-vision-ob`, install again from `ob-labs/ai-vision-skills` for the same scope and selected agent. Check the installation summary and local copies before removing the old source. `skills update` follows the recorded origin and does not switch repositories automatically. Do not remove unrelated Skills or overwrite local customizations without reviewing them.

## Distribution phases

During the pre-open-source period, restricted Daily downloads resolve to an exact published `delivery-v<product-version>` prerelease in this private repository. The current target is `delivery-v0.0.1-daily.20261028.2`, with Linux x64 and ARM64 CLI archives and `linux/amd64` plus `linux/arm64` images. Check that the exact Release is published and its required assets exist before installing; catalog text does not establish publication. An absent Release or unsupported platform stops the download flow.

This revision allows exactly seven Release assets: `aiv-linux-x64.tar.gz`, `aiv-linux-arm64.tar.gz`, `install-aiv.sh`, `release-manifest.json`, `release-images.vars.yaml`, `release-seekdb.vars.yaml`, and `SHA256SUMS`. Private downloads use the operator's authenticated `gh` account. `aiv --version` remains the product version, without `delivery-v`. The first x86-only release, `delivery-v0.0.1-daily.20261028`, was completed before ARM work; its six assets and image references remain unchanged.

Application images use `ghcr.io/ob-labs/ai-vision-skills/{aivision-be,aivision-fe,agentlens,antcollector-gw,signoz-ob}`. Use the manifest's exact digest references and separately verified image access. Optional database mirrors use `oceanbase-ce` and `seekdb` under that namespace only when named in the manifest. Product source and build provenance remain unchanged. Security scanning follows the team's existing offline/manual process.

The native Agent installer runs on the Agent's own Linux x64 or ARM64 machine with the matching bundle. Use Debian Bookworm (glibc 2.36) and check `getconf GNU_LIBC_VERSION` there before onboarding; each release's client evidence records the actual architecture and ABI. The first x86 bundle's minimum required symbol version is glibc 2.35. This client requirement is separate from the static Go CLI and Docker services, whose runtime libraries live inside their images. An older Docker host does not establish native Agent installer compatibility.

After the product becomes open source, product binaries return to the product Release channel and this repository continues to maintain Skills only. Installation commands and Skill names stay the same. Review restricted historical Release assets and temporary credentials before changing repository visibility. See [distribution ownership](docs/distribution.md).

## Development

Read [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md). The checks validate catalog integrity, standalone installation, and the bundled Quickstart runner. They do not establish live platform, model, browser, or deployment compatibility.

## License

The migrated Skill sources retain [Apache-2.0](LICENSE). Product binaries and third-party components retain their own applicable notices and terms; this repository does not redefine their licensing or trial authorization.
