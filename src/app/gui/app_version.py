"""アプリ名・バージョン情報（08_デスクトップアプリ化要件定義書.md 15節）。

APP_VERSION は開発時は "0.0.0-dev" を既定とする。CI（.github/workflows/release.yml）
のビルド時に、Gitタグ（vX.Y.Z）から取得したバージョン番号でこのファイルの
APP_VERSION を書き換えてからPyInstallerビルドを行う。
"""
from __future__ import annotations

APP_NAME = "Document Sites Crawler for RAG"
APP_VERSION = "0.0.0-dev"
