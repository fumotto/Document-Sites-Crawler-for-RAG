"""ConfigLoader（07_CLI仕様.md 3〜5節）。

CLI引数と .env を統合し、検証済みの ConfigRecord を生成する。
優先順位: CLI引数 > .env（環境変数） > デフォルト値
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List, Optional

from src.app.exceptions.errors import ConfigError
from src.app.models.config_record import ConfigRecord

_VALID_MODES = {"incremental", "full"}
_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR"}
_VALID_LOG_FORMATS = {"text", "json"}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crawler",
        description="NotebookLM Document Crawler",
        epilog=(
            "examples:\n"
            "  docker compose run crawler https://react.dev\n"
            "  docker compose run crawler https://react.dev --manifest ./manifest-prod.json\n"
            "  docker compose up\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "url", nargs="?", default=None,
        help="単一サイト処理時の対象URL（省略時は .env の BASE_URLS を使用）",
    )
    parser.add_argument(
        "--manifest", dest="manifest", default=None,
        help="manifest.json の保存先を上書きする（単一サイト処理時のみ）",
    )
    parser.add_argument(
        "--log-level", dest="log_level", default=None,
        help="ログレベルを一時的に上書きする（DEBUG/INFO/WARNING/ERROR）",
    )
    parser.add_argument("--version", action="version", version="crawler 1.0")
    return parser


def _split_lines(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    return [line.strip() for line in raw.splitlines() if line.strip()]


def _split_csv(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _require_env(env: dict, key: str) -> str:
    value = env.get(key)
    if value is None or value == "":
        raise ConfigError(f"{key} is required but not set in .env.")
    return value


def load_config(argv: Optional[List[str]] = None, env: Optional[dict] = None) -> ConfigRecord:
    """CLI引数と環境変数を統合し、ConfigRecord を生成する。

    Raises:
        ConfigError: 引数の組み合わせ不正、必須項目欠落、型不正の場合
    """
    env = dict(env if env is not None else os.environ)
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    base_urls = _split_lines(env.get("BASE_URLS"))

    # --- 5節: 引数バリデーションフロー ---
    if args.url:
        if args.manifest:
            # 単一サイト + manifest上書き
            manifest_override = Path(args.manifest)
        else:
            manifest_override = None
    else:
        if args.manifest:
            raise ConfigError("URL is required when --manifest is specified.")
        if not base_urls:
            raise ConfigError(
                "No target URL found. Specify a URL argument or set BASE_URLS in .env."
            )
        manifest_override = None

    # url も base_urls も存在する場合、CLI引数(url)が優先される（単一サイト処理として確定）
    if args.url:
        base_urls = []

    if args.url and args.manifest and not base_urls:
        # 複数サイト処理時（url省略・BASE_URLS経由）に --manifest を指定した場合はエラー。
        # ここでは args.url が指定されているため単一サイト処理であり問題ない。
        pass

    mode = env.get("MODE", "incremental")
    if mode not in _VALID_MODES:
        raise ConfigError(f'Invalid MODE: {mode}. Expected "incremental" or "full".')

    max_pages_raw = _require_env(env, "MAX_PAGES")
    timeout_raw = _require_env(env, "TIMEOUT_SECONDS")
    try:
        max_pages = int(max_pages_raw)
    except ValueError as exc:
        raise ConfigError(f"MAX_PAGES must be an integer: {max_pages_raw!r}") from exc
    try:
        timeout_seconds = int(timeout_raw)
    except ValueError as exc:
        raise ConfigError(f"TIMEOUT_SECONDS must be an integer: {timeout_raw!r}") from exc

    try:
        word_limit = int(env.get("WORD_LIMIT", "450000"))
    except ValueError as exc:
        raise ConfigError("WORD_LIMIT must be an integer.") from exc

    try:
        request_delay = float(env.get("REQUEST_DELAY", "0.5"))
    except ValueError as exc:
        raise ConfigError("REQUEST_DELAY must be a number.") from exc

    log_level = args.log_level or env.get("LOG_LEVEL", "INFO")
    if log_level not in _VALID_LOG_LEVELS:
        raise ConfigError(f"Invalid --log-level/LOG_LEVEL: {log_level}")

    log_format = env.get("LOG_FORMAT", "text")
    if log_format not in _VALID_LOG_FORMATS:
        raise ConfigError(f"Invalid LOG_FORMAT: {log_format}")

    if args.url and not (args.url.startswith("http://") or args.url.startswith("https://")):
        raise ConfigError(f"Invalid URL: {args.url}")

    return ConfigRecord(
        url=args.url,
        base_urls=base_urls,
        manifest_path_override=manifest_override,
        mode=mode,
        word_limit=word_limit,
        request_delay=request_delay,
        user_agent=env.get("USER_AGENT", "NotebookLM-Crawler/1.0"),
        include=_split_csv(env.get("INCLUDE")),
        exclude=_split_csv(env.get("EXCLUDE")),
        max_pages=max_pages,
        timeout_seconds=timeout_seconds,
        log_level=log_level,
        log_format=log_format,
        log_file_path=Path(env.get("LOG_FILE_PATH", "logs/crawler.log")),
    )
