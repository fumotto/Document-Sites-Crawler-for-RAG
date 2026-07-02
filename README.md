# NotebookLM Document Crawler

Webサイト上のドキュメントを収集・整形し、NotebookLMへアップロードしやすいMarkdownファイル群を生成するツールです。

設計書は `docs/` を参照してください（`02_基本設計書.md` が全体の統合版です）。

## セットアップ

```bash
cp .env.example .env
# .env を編集し、MAX_PAGES / TIMEOUT_SECONDS 等を設定してください（必須項目です）
```

## 実行方法

```bash
# 単一サイト処理
docker compose run crawler https://react.dev

# manifest保存先を変更して単一サイト処理
docker compose run crawler https://react.dev --manifest ./manifest-prod.json

# 複数サイト処理（.env の BASE_URLS を使用）
docker compose up

# ログレベルを一時的に変更
docker compose run crawler https://react.dev --log-level DEBUG
```

## 終了コード

| コード | 意味 |
|---|---|
| 0 | 正常終了 |
| 1 | 致命的エラー（未実行） |
| 2 | 部分的失敗（1つ以上のサイトでビルド不能） |

## テスト

```bash
uvx pip install -r requirements.txt
uvx pip install -r requirements-dev.txt
uvx pytest tests/
```

## ディレクトリ構成

`03_ディレクトリ構成.md` を参照してください。
