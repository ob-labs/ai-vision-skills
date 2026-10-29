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

For this restricted trial, use `delivery-v0.0.1-daily.20261029` in this private repository. It selects Linux x64 or ARM64 CLI archives and matching service images. **The target is available only after its exact prerelease is published and all seven assets are verified.** An absent or draft Release stops installation without replacing an installed binary. Older trial Releases are retired after the replacement is verified; a historical tag or reader does not guarantee a download.

The new target allows exactly seven Release assets: `aiv-linux-x64.tar.gz`, `aiv-linux-arm64.tar.gz`, `install-aiv.sh`, `release-manifest.json`, `release-images.vars.yaml`, `release-seekdb.vars.yaml`, and `SHA256SUMS`. Each installed Skill includes its own CLI download instructions: the same command detects the CLI machine with `uname`, downloads its checksummed archive, and preserves an installed binary on failure. Docker selects the native service child from the pinned multi-platform image index on the deployment daemon's platform. The CLI machine, Docker host and native Agent machine can be different machines. Private downloads use the operator's authenticated `gh` account; `aiv --version` remains the product version, without `delivery-v`.

The native CLI excludes legacy first-party Python resources at link time. The earlier `delivery-v0.0.1-daily.20261028` Release was withdrawn because its CLI embeds legacy Python deployment helpers; it is rejected as a strict native delivery. Source, component build identities and workflow provenance remain product-owned, including any genuinely reused components from an earlier build.

The five private application packages use `ghcr.io/ob-labs/ai-vision-skills/{aivision-be,aivision-fe,agentlens,antcollector-gw,signoz-ob}`. Each accepted release uses its immutable full product-version tag, such as `:0.0.1-daily.20261029`; `:daily` follows the latest accepted Daily. Both platforms share the same version/index reference. Short `:daily.<date>` tags are not published. Deploy with the exact manifest digests and separately verified image access. OceanBase CE and seekdb use fixed official upstream digest references from the selected manifest and vars; confirm those upstream manifests include the actual Docker host platform. This namespace has no database packages, and databases are not republished with each Daily.

Use the selected Release's matching vars when deploying or upgrading. Merge them into an existing deployment's private configuration while preserving credentials, datastore choice and retained data. Saved private database-mirror references must be replaced with the matching upstream references. See [distribution ownership](docs/distribution.md) for delivery and historical-retirement details. Requested x86 and ARM scan bundles contain the five service images only; database dependencies remain separate, and packaging is not a vulnerability-scan result.

For native Agent onboarding, verify that the selected backend serves the Agent's own Linux x64 or ARM64 installer target. Those bundles require glibc 2.35 or newer; Debian Bookworm/glibc 2.36 is the recorded client baseline. Check `getconf GNU_LIBC_VERSION` on the Agent machine. This client requirement is separate from the static Go CLI and Docker services, whose runtime libraries live inside their images. A CLI or image platform declaration does not establish client, Kubernetes or runtime qualification.

After the product becomes open source, product binaries return to the product Release channel and this repository continues to maintain Skills only. Installation commands and Skill names stay the same. Review restricted historical Release assets and temporary credentials before changing repository visibility. See [distribution ownership](docs/distribution.md).

## Development

Read [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md). The checks validate catalog integrity, standalone installation, and the bundled Quickstart runner. They do not establish live platform, model, browser, or deployment compatibility.

## License

The migrated Skill sources retain [Apache-2.0](LICENSE). Product binaries and third-party components retain their own applicable notices and terms; this repository does not redefine their licensing or trial authorization.
