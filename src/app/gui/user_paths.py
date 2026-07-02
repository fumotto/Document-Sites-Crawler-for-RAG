"""データ保存先パス解決（08_デスクトップアプリ化要件定義書.md 8節）。

ルートパスは %USERPROFILE% 直下（例: C:\\Users\\{username}\\DocumentSitesCrawlerForRAG\\）
とする。cache/output/archives/logs の内部構造は03_ディレクトリ構成.mdの定義を
そのまま維持し、ルートパスの決定方法のみをDocker版（カレントディレクトリ直下）
から変更する。
"""
from __future__ import annotations

from pathlib import Path

# フォルダ名はアプリ名「Document Sites Crawler for RAG」のスペース無し表記。
# レジストリ・ファイルパスとして扱いやすいよう英数字のみで構成する。
APP_DATA_FOLDER_NAME = "DocumentSitesCrawlerForRAG"


def get_app_data_root() -> Path:
    """%USERPROFILE%\\DocumentSitesCrawlerForRAG\\ を返す（存在しなければ作成する）。

    Windows以外（開発時のLinux/Mac環境）では Path.home() 配下に同名フォルダを作成する。
    """
    root = Path.home() / APP_DATA_FOLDER_NAME
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_settings_path() -> Path:
    return get_app_data_root() / "settings.json"


def get_cache_root() -> Path:
    path = get_app_data_root() / "cache"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_output_root() -> Path:
    path = get_app_data_root() / "output"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_archives_root() -> Path:
    path = get_app_data_root() / "archives"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_logs_root() -> Path:
    path = get_app_data_root() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_log_file_path() -> Path:
    return get_logs_root() / "crawler.log"
