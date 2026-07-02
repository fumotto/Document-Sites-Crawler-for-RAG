"""ログ設定（07_CLI仕様.md 7節）。

コンソール（標準出力）と logs/crawler.log（追記、RotatingFileHandler）の
両方に同一内容を出力する。
"""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_TEXT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def setup_logging(log_level: str, log_format: str, log_file_path: Path) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))

    # 既存ハンドラをクリアする（再実行・テスト時の重複登録防止）
    root_logger.handlers.clear()

    if log_format == "json":
        formatter: logging.Formatter = _JsonFormatter()
    else:
        formatter = logging.Formatter(_TEXT_FORMAT, datefmt=_DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        str(log_file_path), maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8",
    )
    if not log_file_path.exists():
        log_file_path.touch()
    try:
        os.chmod(log_file_path, 0o666 if os.name == "nt" else 0o644)
    except OSError:
        pass
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        import json

        payload = {
            "timestamp": self.formatTime(record, _DATE_FORMAT),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)
