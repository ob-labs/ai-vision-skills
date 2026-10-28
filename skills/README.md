# Skills

Curated [agent skills](https://github.com/vercel-labs/skills) for working with AI
Vision. A skill is a directory holding a `SKILL.md` — YAML front matter with a
`name` and a `description`, plus a Markdown body — and optional supporting files
such as a `reference/` directory for depth. A coding agent reads the
`description` to decide when the skill applies, then reads the body and follows
its links.

## Prerequisites by workflow

Installing a Skill installs its instructions and bundled resources. It does not
deploy the platform or connect an Agent automatically. `aivision-quickstart`
reuses an existing instance and runs its bundled Python SDK demo; follow its
[workflow](aivision-quickstart/reference/workflow.md) for the runtime, private
model credentials, platform access, and browser setup/readback steps.

Deployment and query Skills use the `aiv` CLI. Each checks its prerequisites
and guides CLI installation on the machine where its commands will run.

Start with `command -v aiv` and `aiv --version` in that terminal. If `aiv` is
already in `~/.local/bin`, restore that directory to PATH before downloading
another copy. Keep the PATH setting in the active shell's startup file and
check again in a new terminal. Installation and recovery steps are bundled in
[`aivision-deploy`'s prerequisites](aivision-deploy/reference/prerequisites.md),
[`aivision-trace`'s install guide](aivision-trace/reference/install-cli.md), and
[`aivision-metric`'s install guide](aivision-metric/reference/install-cli.md).

Use the machine appropriate to the task: deployment commands run on the
deployment host, queries can run on any machine that can reach the existing
platform, and `aiv connect` runs on the machine running the Agent. Remote users
need a reachable platform URL; their `127.0.0.1` refers to their own machine.
Querying existing telemetry needs query access, not another deployment or a
local collection plugin.

## Install

### Via `npx skills`

```bash
# One skill, into the current project
npx skills add ob-labs/ai-vision-skills --skill aivision-deploy

# Guided first use with a test Agent, installed under your home directory
npx skills add ob-labs/ai-vision-skills --skill aivision-quickstart --global

# All skills, for all agents (no prompts)
npx skills add ob-labs/ai-vision-skills --all
```

Add `--global` to install under `$HOME` instead of the current project, and
`--agent <id>` — for example `claude-code` — to target one agent explicitly.
Otherwise, the installer detects installed agents or prompts you to select
targets. Interactive installation offers symlinks from agent directories to a
shared canonical copy, or independent copies. `--all` selects all skills and
all agents without prompting. See the upstream
[installation methods](https://github.com/vercel-labs/skills#installation-methods).

During the restricted trial, only authorized repository users can install.
The command clones this Skills repository using the caller's own authorized
GitHub/Git session; do not distribute shared tokens. An authorized operator may
also make the complete manual copy below. Restricted Daily CLI and deployment
metadata use an exact published `delivery-v<product-version>` prerelease in this
repository. The current target, `delivery-v0.0.1-daily.20261028.2`, allows only the
Linux x64 CLI and `linux/amd64` images; verify publication and assets before use.
Missing assets or another host platform require a compatible published delivery,
not a product checkout. Stable product Releases retain their original channel.
Installing a Skill, downloading a CLI Release, pulling platform images, and
signing in to AI Vision are separate operations; authenticate only the one that
actually requires access.

### Manual copy

Copy the skill directory into the agent's skills directory — `.claude/skills`,
`.codex/skills`, `.cursor/skills` or `.agents/skills`, in the project or under
`$HOME`:

```bash
mkdir -p "$HOME/.claude/skills"
cp -R skills/aivision-deploy "$HOME/.claude/skills/"
```

Copy the whole directory, not just `SKILL.md`: bundled references, scripts,
dependency lists, and tests are part of the Skill. Run the copy from the
repository root and check an existing installed copy before replacing it. A
separately installed Skill does not include the repository's CLI source; Skills
that need the CLI provide Release installation instructions.

Deployment leaves `aiv` installed in a permanent directory with supported-shell
PATH setup verified in a fresh terminal. Normal deployment and maintenance use
the CLI directly, retaining the original target and identity/configuration
selectors; no task-local `manage` wrapper is needed.

## Available Skills

| Skill | Purpose |
|---|---|
| [`aivision-quickstart`](aivision-quickstart/SKILL.md) | Reuse an existing platform, configure a model, and run a test Agent with real requests, Trace/Session readback, and diagnosis |
| [`aivision-deploy`](aivision-deploy/SKILL.md) | Deploy, verify and upgrade the whole AI Vision stack with `aiv`, preserving the target (Docker, optional Compose or Kubernetes), datastore and deployment identity |
| [`aivision-trace`](aivision-trace/SKILL.md) | Query, inspect and export LLM traces with `aiv query`, and compose those exports into an evaluation dataset |
| [`aivision-metric`](aivision-metric/SKILL.md) | Query complete time-window trace metrics with usage coverage; inspect SQL capabilities or use verified details for custom analysis |

## From first requests to querying

Use `aivision-quickstart` to create a test workload and experience model setup,
real requests, Trace/Session readback, and diagnosis on an existing deployment.
Its demo makes four real model calls; connection tests, model validation, and
LLM diagnosis have separate calls and costs. Keep model credentials in private
local configuration.

Once AI Vision receives telemetry, the query Skills let your coding agent work
with that data. Start with the question you want answered:

| You want to… | Skill and example request |
|---|---|
| Set up a model and experience real requests with a test Agent | `aivision-quickstart`: “Use my existing AI Vision platform at https://vision.example.com. I will provide my model credentials privately. Create a test Agent, send four real requests, and inspect Traces, Sessions, and diagnosis records, including failed or inapplicable checks.” |
| Find a slow or failed request, follow its spans/session, or export traces | `aivision-trace`: “找出这个 Agent 最近一小时最慢的请求，展开 span 和会话上下文，并导出选中的 Trace。” |
| Review request volume, errors, latency or usage | `aivision-metric`: “统计这个 Agent 最近一天的请求量、错误率、P95 延迟和 Token 用量；有成本数据时一起统计。” |

For an empty deployment, use Quickstart for a test Agent or connect your own
Agent through onboarding and run a real task first. For an existing workload,
use the CLI profile for the correct platform endpoint, space and Agent. Query access uses a space-scoped SpaceKey;
account login and Agent ingest credentials alone are not sufficient. Token and
cost results depend on the fields and coverage actually reported.

Quickstart, deployment, and query Skills can be installed separately. Add either
query Skill with:

```bash
npx skills add ob-labs/ai-vision-skills --skill aivision-trace
npx skills add ob-labs/ai-vision-skills --skill aivision-metric
```

The [installation options](#install) also apply to these skills. Installing or
running a query skill is optional; deployment verification does not run these
analyses or export application data automatically.

## Layout

```
skills/
├── README.md
├── aivision-quickstart/
│   ├── SKILL.md
│   ├── scripts/
│   │   ├── run_demo.py
│   │   └── requirements.txt
│   ├── reference/
│   │   └── workflow.md
│   └── tests/
│       └── test_run_demo.py
├── aivision-deploy/
│   ├── SKILL.md              # entry point: what the agent reads first
│   └── reference/            # depth, read on demand from SKILL.md
│       ├── docker.md
│       ├── kubernetes.md
│       ├── prerequisites.md
│       ├── operations.md
│       └── upgrade.md
├── aivision-trace/
│   ├── SKILL.md
│   └── reference/
│       ├── install-cli.md
│       ├── query-setup.md
│       ├── path-setup.md
│       └── dataset-export.md
└── aivision-metric/
    ├── SKILL.md
    └── reference/
        ├── install-cli.md
        ├── query-setup.md
        ├── path-setup.md
        ├── query-capabilities.md
        └── local-aggregation.md
```

Keep `SKILL.md` short enough to read in one pass: it carries the decision the
agent must make, the commands and interactions to perform, the verification that
proves it worked, and rules that must not be broken. Background, variants and long command blocks
belong in `reference/`, linked from the entry point.

## Update & Remove

Re-run the install command after updating a skill, or replace the copied
directory. To remove one, delete its directory from the agent's skills directory.
