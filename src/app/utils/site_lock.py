"""サイト単位の排他ロック（06_処理シーケンス.md 9節）。

cache/{site_identifier}/.lock を用いた排他ロック。取得失敗時は待機せず
即座に LockAcquisitionError を送出する（キュー化は行わない）。
"""
from __future__ import annotations

import errno
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from src.app.exceptions.errors import LockAcquisitionError

try:
    import fcntl  # type: ignore

    _HAS_FCNTL = True
except ImportError:  # Windows等 fcntl が存在しない環境
    _HAS_FCNTL = False


@contextmanager
def site_lock(lock_path: Path) -> Iterator[None]:
    """指定パスのロックファイルを排他取得する。処理完了後は必ず解放する。"""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)
    try:
        if _HAS_FCNTL:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                if exc.errno in (errno.EACCES, errno.EAGAIN):
                    raise LockAcquisitionError(
                        f"Failed to acquire lock: {lock_path} (already running?)"
                    ) from exc
                raise
        else:
            # fcntl非対応環境向けの簡易フォールバック（PID書き込みによる簡易排他）
            os.lseek(fd, 0, os.SEEK_SET)
            existing = os.read(fd, 64)
            if existing.strip():
                raise LockAcquisitionError(
                    f"Failed to acquire lock: {lock_path} (already running?)"
                )
            os.write(fd, str(os.getpid()).encode("utf-8"))
        yield
    finally:
        if _HAS_FCNTL:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
        else:
            try:
                os.ftruncate(fd, 0)
            except OSError:
                pass
        os.close(fd)
