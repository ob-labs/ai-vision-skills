# AI Vision Skills

[English](README.md) · [简体中文](README.zh-CN.md) · 日本語

Codex、Claude Code などの対応エージェントで、AI Vision のデプロイ、最初のトレースの生成、テレメトリの確認ができます。

## `npx skills` でインストール

プロジェクトのディレクトリで次のコマンドを実行します。リポジトリへのアクセスが制限されている場合は、アクセス権のある自分の GitHub 認証情報を使ってください。

```bash
npx skills add ob-labs/ai-vision-skills --list
npx skills add ob-labs/ai-vision-skills --skill aivision-deploy --agent codex
```

`aivision-deploy` を使いたいスキル名に置き換えます。`--agent` を省略すると対話形式でエージェントを選べます。`--global` を付けると、同じユーザーの複数のプロジェクトで使えます。手動でインストールする場合は、スキルのディレクトリ全体をエージェントのスキル用ディレクトリにコピーします。

## スキルを選ぶ

| スキル | 用途 |
| --- | --- |
| [aivision-deploy](skills/aivision-deploy/SKILL.md) | AI Vision のデプロイやアップグレード、サービスの動作確認、初回のユーザー登録と利用開始を支援します。 |
| [aivision-quickstart](skills/aivision-quickstart/SKILL.md) | 稼働中の AI Vision で、画面のガイドまたはエージェントによるデモを使い、最初のトレースやセッションを確認します。 |
| [aivision-trace](skills/aivision-trace/SKILL.md) | トレースを検索し、スパンやセッションの情報を確認したり、選んだトレースをエクスポートしたりできます。 |
| [aivision-metric](skills/aivision-metric/SKILL.md) | リクエスト数、エラー、レイテンシを確認します。データがある場合はトークン使用量やコストも確認できます。 |

インストール後は、会話でスキル名を指定します。たとえば「`aivision-quickstart` を使って、稼働中の AI Vision で最初のトレースを生成し、確認したい」と依頼します。

このリポジトリではスキルとその付属ファイルを配布します。製品のバイナリやデプロイ用のファイルは [AI Vision Releases](https://github.com/antgroup/ai-vision/releases) で確認できます。

[コントリビューションガイド](CONTRIBUTING.md) · [Apache-2.0](LICENSE)
