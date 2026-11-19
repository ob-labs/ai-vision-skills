# AI Vision Skills

[English](README.md) · 简体中文 · [日本語](README.ja-JP.md)

在 Codex、Claude Code 或其他兼容的 Agent 中使用这些技能，部署 AI Vision、生成第一条 Trace，并查看可观测数据。

## 通过 `npx skills` 安装

使用 Node.js 22.20 或更高版本，在项目目录中运行以下命令。

```bash
npx skills add ob-labs/ai-vision-skills --list
npx skills add ob-labs/ai-vision-skills --skill aivision-deploy --agent codex
```

将 `aivision-deploy` 换成所需的技能名称。省略 `--agent` 可交互选择 Agent，加上 `--global` 可在当前用户的多个项目中使用。手动安装时，将整个技能目录复制到 Agent 的技能目录。

## 选择技能

| 技能 | 用途 |
| --- | --- |
| [aivision-deploy](skills/aivision-deploy/SKILL.md) | 安装 All-in-One 个人版，部署或升级共享实例，并引导用户注册、查看第一条 Trace。 |
| [aivision-quickstart](skills/aivision-quickstart/SKILL.md) | 在已有实例中使用平台引导或让 Agent 带跑示例，查看第一批 Trace 和会话。 |
| [aivision-trace](skills/aivision-trace/SKILL.md) | 查找 Trace，检查 Span 和会话上下文，或导出选中的 Trace。 |
| [aivision-metric](skills/aivision-metric/SKILL.md) | 查看请求量、错误和延迟，以及数据覆盖范围内的 Token 用量和成本。 |

安装后，直接在对话中指定技能名称。例如：“用 `aivision-quickstart` 帮我在已有的 AI Vision 实例中生成并查看第一条 Trace。”

本仓库提供技能及配套资源。请到 [AI Vision Releases](https://github.com/antgroup/ai-vision/releases) 查看适用于你所用平台的产品二进制文件和部署包。

[参与维护](CONTRIBUTING.md) · [Apache-2.0](LICENSE)
