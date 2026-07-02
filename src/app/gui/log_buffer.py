"""ログバッファ（08_デスクトップアプリ化要件定義書.md 5.4, 5.5節）。

logging.Handler としてルートロガーに追加し、logs/crawler.log への書き込みと
同時にスレッドセーフなリングバッファへログを蓄積する。JS側はポーリングにより
`get_lines_since(index)` を呼び出し、前回取得以降の差分ログのみを受け取る。
"""
from __future__ import annotations

import logging
import threading
from collections import deque
from dataclasses import dataclass
from typing import List

DEFAULT_MAX_LINES = 5000  # IMPL-3: 直近5,000行程度をリングバッファで保持


@dataclass
class LogEntry:
    index: int
    text: str


class InMemoryLogHandler(logging.Handler):
    """logging.Handler実装。フォーマット済みログ行をリングバッファへ蓄積する。"""

    def __init__(self, max_lines: int = DEFAULT_MAX_LINES):
        super().__init__()
        self._lock = threading.Lock()
        self._buffer: deque = deque(maxlen=max_lines)
        self._next_index = 0

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
        except Exception:
            message = record.getMessage()

        with self._lock:
            entry = LogEntry(index=self._next_index, text=message)
            self._buffer.append(entry)
            self._next_index += 1

    def get_lines_since(self, since_index: int) -> List[LogEntry]:
        """since_index より大きいindexを持つログ行のみを返す（差分取得）。"""
        with self._lock:
            return [e for e in self._buffer if e.index > since_index]

    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()
            self._next_index = 0
