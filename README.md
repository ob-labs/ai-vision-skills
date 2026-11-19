# AI Vision Skills

English · [简体中文](README.zh-CN.md) · [日本語](README.ja-JP.md)

Use these skills in Codex, Claude Code, or another compatible agent to deploy AI Vision, generate your first traces, and explore telemetry.

## Install with `npx skills`

Run these commands from your project directory. If GitHub restricts access to the catalog, use your own authorized GitHub credentials.

```bash
npx skills add ob-labs/ai-vision-skills --list
npx skills add ob-labs/ai-vision-skills --skill aivision-deploy --agent codex
```

Replace `aivision-deploy` with the skill you need. Omit `--agent` to choose interactively, or add `--global` to install for your user account across projects. For a manual install, copy the complete skill directory into your agent's skills directory.

## Choose a skill

| Skill | What it helps you do |
| --- | --- |
| [aivision-deploy](skills/aivision-deploy/SKILL.md) | Deploy or upgrade AI Vision, check the services, and guide the first user through sign-up and onboarding. |
| [aivision-quickstart](skills/aivision-quickstart/SKILL.md) | Try an existing AI Vision instance with the platform guide or an agent-led demo, then inspect your first traces and sessions. |
| [aivision-trace](skills/aivision-trace/SKILL.md) | Find a trace, inspect spans and session context, or export selected traces. |
| [aivision-metric](skills/aivision-metric/SKILL.md) | Review request volume, errors, latency, token usage, and cost where data is available. |

Once installed, ask your agent to use the skill by name. For example, “Use `aivision-quickstart` to help me generate and inspect my first trace on my AI Vision instance.”

This catalog distributes the skill instructions and their bundled resources. Download product binaries and deployment artifacts from [AI Vision Releases](https://github.com/antgroup/ai-vision/releases).

[Contributing](CONTRIBUTING.md) · [Apache-2.0](LICENSE)
