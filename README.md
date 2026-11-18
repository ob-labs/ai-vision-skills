# AI Vision Skills

The maintained AI Vision Skill catalog for deploying the platform, trying an Agent, inspecting traces, and querying usage. This repository is the canonical source for these Skills. Product source, CLI builds, deployments, and telemetry plugin implementation are maintained by `antgroup/ai-vision`.

## Choose how to get started

- **Quick trial or personal use** on a compatible Linux Docker host: start with the [All-in-One Preview](skills/aivision-deploy/reference/all-in-one.md). Run the installer directly or ask a coding Agent to use the deployment Skill. If your preview includes the sample helper, send a synthetic Trace after sign-up.
- **Shared deployment or an external database**: follow the [distributed deployment guide](skills/aivision-deploy/SKILL.md) for Docker, Compose, or Kubernetes on a supported host.
- **Already running AI Vision**: keep your deployment and use [Quickstart](skills/aivision-quickstart/SKILL.md) to try a test Agent and view its Traces.

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
| [aivision-deploy](skills/aivision-deploy/SKILL.md) | Install the All-in-One Preview or deploy, verify, and upgrade the distributed platform |
| [aivision-quickstart](skills/aivision-quickstart/SKILL.md) | Reuse an existing platform, configure a model, and exercise real requests with a test Agent |
| [aivision-trace](skills/aivision-trace/SKILL.md) | Query and inspect traces and export selected data |
| [aivision-metric](skills/aivision-metric/SKILL.md) | Query latency, errors, usage, and available cost metrics |

Copy the complete Skill directory for manual installation: `SKILL.md`, references, scripts, requirements, and agent metadata belong together. Each Skill can be installed independently. See the [catalog guide](skills/README.md) for prerequisites and workflow selection.

## Existing installations

If you installed the Skills from a different source, install from `ob-labs/ai-vision-skills` again for the same scope and selected agent. Check the installation summary and local copies before removing the old source. `skills update` follows the recorded origin and does not switch repositories automatically. Do not remove unrelated Skills or overwrite local customizations without reviewing them.

## Product distributions

Distributed deployments and `aiv` CLI downloads use exact, published Stable
or Daily assets from the [AI Vision product releases](https://github.com/antgroup/ai-vision/releases).
Use the matching CLI, checksummed manifest, and datastore vars. The five product
packages live under `ghcr.io/antgroup/ai-vision/` as `frontend`, `backend`,
`ingest-gateway`, `diagnosis`, and `data-backend`. The deployment daemon and Agent
client must each match their own architecture and runtime requirements.

For personal use on a compatible Linux Docker host, follow the
[All-in-One guide](skills/aivision-deploy/reference/all-in-one.md) when an exact
verified bundle is available. Historical restricted previews retain their own
versions and qualification. See [distribution ownership](docs/distribution.md).

## Development

Read [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md). The checks validate catalog integrity, standalone installation, and the bundled Quickstart runner. They do not establish live platform, model, browser, or deployment compatibility.

## License

The migrated Skill sources retain [Apache-2.0](LICENSE). Product binaries and third-party components retain their own applicable notices and terms; this repository does not redefine their licensing or trial authorization.
