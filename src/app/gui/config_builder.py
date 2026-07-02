"""フォーム入力 → ConfigRecord 変換（08_デスクトップアプリ化要件定義書.md IMPL-1）。

既存の ConfigLoader.load_config() は CLI引数(argv)・環境変数(.env) を前提とした
実装であるため、GUIのフォーム入力を無理にargv形式へ変換するのではなく、
GUI専用の変換関数として新設する。CLIとGUIは最終的に同じ ConfigRecord を
組み立てる点で処理ロジックを共有する（Orchestrator以降は完全に共通）。
"""
from __future__ import annotations

from typing import Any, Dict, List

from src.app.exceptions.errors import ConfigError
from src.app.gui.user_paths import get_log_file_path
from src.app.models.config_record import ConfigRecord

_VALID_MODES = {"incremental", "full"}
_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR"}


def _split_lines(raw: str) -> List[str]:
    return [line.strip() for line in (raw or "").splitlines() if line.strip()]


def _split_csv(raw: str) -> List[str]:
    return [item.strip() for item in (raw or "").split(",") if item.strip()]


def build_config_from_form(form_data: Dict[str, Any]) -> ConfigRecord:
    """4.2節の入力項目からConfigRecordを組み立てる。

    Raises:
        ConfigError: URL未入力、値の型不正等
    """
    urls = _split_lines(form_data.get("urls_text", ""))
    if not urls:
        raise ConfigError("対象URLを1つ以上入力してください。")

    # 4.2節: 1行のみなら単一サイト処理、複数行なら複数サイト処理として扱う
    if len(urls) == 1:
        url = urls[0]
        base_urls: List[str] = []
    else:
        url = None
        base_urls = urls

    for u in urls:
        if not (u.startswith("http://") or u.startswith("https://")):
            raise ConfigError(f"URLの形式が不正です: {u}")

    mode = form_data.get("mode", "incremental")
    if mode not in _VALID_MODES:
        raise ConfigError(f"MODEの値が不正です: {mode}")

    try:
        word_limit = int(form_data.get("word_limit", 450000))
        max_pages = int(form_data.get("max_pages", 1000))
        timeout_seconds = int(form_data.get("timeout_seconds", 30))
        request_delay = float(form_data.get("request_delay", 0.5))
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"数値項目の入力値が不正です: {exc}") from exc

    log_level = form_data.get("log_level", "INFO")
    if log_level not in _VALID_LOG_LEVELS:
        raise ConfigError(f"ログレベルの値が不正です: {log_level}")

    return ConfigRecord(
        url=url,
        base_urls=base_urls,
        manifest_path_override=None,  # GUIでは提供しない（上級者向けCLI専用機能）
        mode=mode,
        word_limit=word_limit,
        request_delay=request_delay,
        user_agent="DocumentSitesCrawlerForRAG/1.0",
        include=_split_csv(form_data.get("include", "")),
        exclude=_split_csv(form_data.get("exclude", "")),
        max_pages=max_pages,
        timeout_seconds=timeout_seconds,
        log_level=log_level,
        log_format="text",
        log_file_path=get_log_file_path(),
    )
