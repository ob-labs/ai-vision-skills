# AI Vision Skills

[English](README.md) · [简体中文](README.zh-CN.md) · 日本語

Codex、Claude Code などの対応エージェントで、AI Vision のデプロイ、最初のトレースの生成、テレメトリの確認ができます。

## `npx skills` でインストール

Node.js 22.20 以降を使い、プロジェクトのディレクトリで次のコマンドを実行します。

```bash
npx skills add ob-labs/ai-vision-skills --list
npx skills add ob-labs/ai-vision-skills --skill aivision-deploy --agent codex
```

`aivision-deploy` を使いたいスキル名に置き換えます。`--agent` を省略すると対話形式でエージェントを選べます。`--global` を付けると、同じユーザーの複数のプロジェクトで使えます。手動でインストールする場合は、スキルのディレクトリ全体をエージェントのスキル用ディレクトリにコピーします。

## スキルを選ぶ

| スキル | 用途 |
| --- | --- |
| [aivision-deploy](skills/aivision-deploy/SKILL.md) | All-in-One 個人版のセットアップや共有インスタンスの導入・アップグレードを支援します。ユーザー登録から最初のトレースの確認まで進めます。 |
| [aivision-quickstart](skills/aivision-quickstart/SKILL.md) | 稼働中の AI Vision で、画面のガイドまたはエージェントによるデモを使い、最初のトレースやセッションを確認します。 |
| [aivision-trace](skills/aivision-trace/SKILL.md) | トレースを検索し、スパンやセッションの情報を確認したり、選んだトレースをエクスポートしたりできます。 |
| [aivision-metric](skills/aivision-metric/SKILL.md) | リクエスト数、エラー、レイテンシを確認します。データがある場合はトークン使用量やコストも確認できます。 |

インストール後は、会話でスキル名を指定します。たとえば「`aivision-quickstart` を使って、稼働中の AI Vision で最初のトレースを生成し、確認したい」と依頼します。

このリポジトリではスキルと付属ファイルを配布します。お使いの環境に対応する製品バイナリやデプロイ用のパッケージは [AI Vision Releases](https://github.com/antgroup/ai-vision/releases) で確認できます。

[コントリビューションガイド](CONTRIBUTING.md) · [Apache-2.0](LICENSE)
