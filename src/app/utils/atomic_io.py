"""アトミックなJSON書き込みユーティリティ（06_処理シーケンス.md 9節）。

同一ディレクトリ内に一時ファイルを作成して書き込んだ後、os.replace で
本来のファイル名に置き換える。書き込み途中の異常終了でファイルが破損した
状態で残ることを防ぐ。
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def _file_mode() -> int:
    return 0o666 if os.name == "nt" else 0o644


def _ensure_readable_file(fd: int) -> None:
    try:
        os.fchmod(fd, _file_mode())
    except (AttributeError, NotImplementedError, PermissionError):
        pass


def _atomic_write(path: Path, writer: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            _ensure_readable_file(f.fileno())
            writer(f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
        os.chmod(path, _file_mode())
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def atomic_write_json(path: Path, data: Any) -> None:
    _atomic_write(path, lambda f: json.dump(data, f, ensure_ascii=False, indent=2))


def atomic_write_text(path: Path, text: str) -> None:
    _atomic_write(path, lambda f: f.write(text))


def read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
