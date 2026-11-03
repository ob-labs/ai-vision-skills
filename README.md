# AI Vision Skills

The maintained AI Vision Skill catalog for deploying the platform, trying an Agent, inspecting traces, and querying usage. This repository is the canonical source for these Skills. Product Release and Daily downloads are selected from `ob-labs/ai-vision-ob`; historical private deliveries remain retained here. Product source, CLI builds, canonical deployment assets, and telemetry plugin implementation remain in the product repository.

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

## Product downloads and historical delivery

Skill installation continues to use `ob-labs/ai-vision-skills`; product/CLI
source, builds, deployment assets and binary Releases belong to
`ob-labs/ai-vision-ob`. Each independently installed Skill includes the same
self-contained CLI recipe. Select a published immutable product tag explicitly:
`v<version>` for Release or `v<version>-daily.<YYYYMMDD>[.<N>]` for Daily/preview.
There is no assumed published `0.1.0` Daily date. A missing version, draft,
checksum mismatch or unavailable host archive stops before replacing the CLI.

The standard source-compatible CLI is the default profile. Read the selected
Release's actual manifest and matching vars; do not apply a restricted native
variant's settings to it. The recipes use anonymous `curl` downloads for public
Releases, with `jq` for JSON validation and authenticated `gh` fallback while
the product repository is private. Git access, Release access, image pulls,
platform login, SpaceKeys and model credentials are separate operations.

The selected manifest pins all five service images and fixed upstream database
dependencies. The product publishes its four application images; SigNoz remains
owned by `ob-labs/signoz` and is consumed by digest. Do not infer namespaces or
platform support from a tag or CLI architecture. Merge the verified CE or seekdb
vars into existing private configuration, retaining credentials, datastore,
history and data identity. Saved retired database-mirror references require the
selected upstream references. Runtime and platform qualification must come from
the actual Release's evidence.

Historical `delivery-v` Releases and private `ai-vision-skills` packages are
explicit compatibility paths, with their original tag/platform/asset guards.
They are not default downloads and are not rewritten or deleted by this
cutover. The withdrawn source-bearing `.20261028` delivery remains rejected;
historical reader support does not establish current availability. See
[distribution ownership](docs/distribution.md) for frozen provenance, retention,
and the remaining publication/visibility steps. Repository visibility remains
unchanged by these instructions.

For native Agent onboarding, inspect the selected backend's own installer and
ABI requirements on the Agent machine. Historical native bundles required
glibc 2.35 or newer; that historical baseline does not qualify another Release,
a different Agent machine, Kubernetes, or a model integration.

## Development

Read [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md). The checks validate catalog integrity, standalone installation, and the bundled Quickstart runner. They do not establish live platform, model, browser, or deployment compatibility.

## License

The migrated Skill sources retain [Apache-2.0](LICENSE). Product binaries and third-party components retain their own applicable notices and terms; this repository does not redefine their licensing or trial authorization.
