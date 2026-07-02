"""設定値の永続化（08_デスクトップアプリ化要件定義書.md 4.3節 / IMPL-4）。

IMPL-4の決定に基づき、内部DTO（ConfigRecord）ではなく、フォーム入力値を
そのままの形でJSONとして保存する。これにより、ConfigRecordのフィールド構成が
将来変更されても settings.json の前方互換性を保ちやすくする。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

from src.app.gui.user_paths import get_settings_path
from src.app.utils.atomic_io import atomic_write_json

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS: Dict[str, Any] = {
    "urls_text": "",
    "mode": "incremental",
    "word_limit": 450000,
    "request_delay": 0.5,
    "include": "",
    "exclude": "",
    "max_pages": 1000,
    "timeout_seconds": 30,
    "log_level": "INFO",
}


def load_settings() -> Dict[str, Any]:
    path = get_settings_path()
    if not path.exists():
        return dict(DEFAULT_SETTINGS)
    try:
        with open(path, "r", encoding="utf-8") as f:
            saved = json.load(f)
        merged = dict(DEFAULT_SETTINGS)
        merged.update(saved)
        return merged
    except (json.JSONDecodeError, OSError):
        logger.warning("Failed to load settings.json; falling back to defaults.", exc_info=True)
        return dict(DEFAULT_SETTINGS)


def save_settings(form_data: Dict[str, Any]) -> None:
    path = get_settings_path()
    merged = dict(DEFAULT_SETTINGS)
    merged.update(form_data)
    atomic_write_json(path, merged)
