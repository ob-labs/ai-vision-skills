# AI Vision Skills

English · [简体中文](README.zh-CN.md) · [日本語](README.ja-JP.md)

Use these skills in Codex, Claude Code, or another compatible agent to deploy AI Vision, generate your first traces, and explore telemetry.

## Install with `npx skills`

Use Node.js 22.20 or later and run these commands from your project directory.

```bash
npx skills add ob-labs/ai-vision-skills --list
npx skills add ob-labs/ai-vision-skills --skill aivision-deploy --agent codex
```

Replace `aivision-deploy` with the skill you need. Omit `--agent` to choose interactively, or add `--global` to install for your user account across projects. For a manual install, copy the complete skill directory into your agent's skills directory.

## Choose a skill

| Skill | What it helps you do |
| --- | --- |
| [aivision-deploy](skills/aivision-deploy/SKILL.md) | Install All-in-One Personal Edition, deploy or upgrade a shared instance, and guide the first user through sign-up and their first Trace. |
| [aivision-quickstart](skills/aivision-quickstart/SKILL.md) | Try an existing AI Vision instance with the platform guide or an agent-led demo, then inspect your first traces and sessions. |
| [aivision-trace](skills/aivision-trace/SKILL.md) | Find a trace, inspect spans and session context, or export selected traces. |
| [aivision-metric](skills/aivision-metric/SKILL.md) | Review request volume, errors, latency, token usage, and cost where data is available. |

Once installed, ask your agent to use the skill by name. For example, “Use `aivision-quickstart` to help me generate and inspect my first trace on my AI Vision instance.”

This catalog contains the skills and their bundled resources. Check [AI Vision Releases](https://github.com/antgroup/ai-vision/releases) for the product binaries and deployment bundles available for your platform.

[Contributing](CONTRIBUTING.md) · [Apache-2.0](LICENSE)
