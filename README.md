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

Discover available [private Releases](https://github.com/ob-labs/ai-vision-skills/releases) using the CLI installation guide bundled with each Skill. The guide identifies the client operating system and hardware, finds a published compatible Daily and pins its exact tag for the download. It also supports selecting an explicit version. Compare the selected product version with the installed CLI or deployment before upgrading.

| Machine or use | Release artifacts to select |
|---|---|
| Linux x64 CLI | The x64 Linux archive from a published base delivery. |
| Linux x64 service deployment | The base manifest and OceanBase CE or seekdb vars for a Linux x64 Docker host. |
| Apple Silicon Mac | The arm64 macOS archive and matching backend vars from the base Daily's macOS assets or a published historical companion for that exact base. |
| Windows x64 client preview | The Windows ZIP from a compatible published base delivery. For Agent onboarding, use the preview backend configuration in a Linux test deployment. |

The current trial covers these platforms. Older Releases may retain additional archives for existing pinned installations. The CLI, Docker host and Agent may run on different machines. Check each platform independently. Private downloads use an authorized `gh` session. The CLI prints the actual product version, and the deployment uses the exact image digests in the selected manifest and vars.

The five private application packages use `ghcr.io/ob-labs/ai-vision-skills/{aivision-be,aivision-fe,agentlens,antcollector-gw,signoz-ob}`. The full product version identifies each accepted delivery. `:daily` follows the latest accepted base Daily. Verify image access separately and confirm that the application and upstream database image manifests include the Docker host architecture.

Use the selected Release's matching vars when deploying or upgrading. Merge them into an existing deployment's private configuration while preserving credentials, datastore choice and retained data. Saved private database-mirror references must be replaced with the matching upstream references. See [distribution ownership](docs/distribution.md) for delivery and historical-retirement details. Requested x86 and ARM scan bundles contain the five service images only; database dependencies remain separate, and packaging is not a vulnerability-scan result.

For Linux Agent onboarding, verify that the selected backend serves the Linux x64 installer. It requires glibc 2.35 or newer. Debian Bookworm/glibc 2.36 is the recorded client baseline. Check `getconf GNU_LIBC_VERSION` on the Agent machine. The static Go CLI and the containerized services have separate runtime requirements.

After the product becomes open source, product binaries return to the product Release channel and this repository continues to maintain Skills only. Installation commands and Skill names stay the same. Review restricted historical Release assets and temporary credentials before changing repository visibility. See [distribution ownership](docs/distribution.md).

## Development

Read [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md). The checks validate catalog integrity, standalone installation, and the bundled Quickstart runner. They do not establish live platform, model, browser, or deployment compatibility.

## License

The migrated Skill sources retain [Apache-2.0](LICENSE). Product binaries and third-party components retain their own applicable notices and terms; this repository does not redefine their licensing or trial authorization.
