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

---

## デスクトップアプリ版（Windows）

詳細仕様は `docs/08_デスクトップアプリ化要件定義書.md` を参照してください。

### ローカルでの起動（開発用）

```bash
uvx pip install -r requirements.txt
uvx pip install -r requirements-desktop.txt
uvx python src/app/gui/desktop_main.py
```

### インストーラのビルド（Windows環境が必要）

```powershell
pip install -r requirements.txt -r requirements-desktop.txt pyinstaller
pyinstaller main.spec
choco install innosetup -y
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DAPP_VERSION="0.0.1" installer.iss
# Output\DocumentSitesCrawlerForRAGSetup.exe が生成される
```

### 自動リリース

`git tag vX.Y.Z && git push --tags` を実行すると、GitHub Actions
（`.github/workflows/release.yml`）が自動的にビルド・GitHub Release作成・
インストーラの添付までを行います。

配布ページ：`docs/index.html`（GitHub Pages、`docs/`フォルダをPages公開元に設定してください）

