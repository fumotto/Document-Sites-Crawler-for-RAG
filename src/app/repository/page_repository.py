"""PageRepository（04_モジュール設計.md 4節 / 05_データ構造設計.md）。

pages/{page_hash}.md の抽出済みMarkdown本文を読み書きする。
本文のみを保存し、メタ情報は保持しない。
"""
from __future__ import annotations

from pathlib import Path

from src.app.utils.atomic_io import atomic_write_text


class PageRepository:
    def __init__(self, pages_dir: Path):
        self._pages_dir = pages_dir

    def _path_for(self, page_hash: str) -> Path:
        return self._pages_dir / f"{page_hash}.md"

    def save(self, page_hash: str, body_markdown: str) -> None:
        atomic_write_text(self._path_for(page_hash), body_markdown)

    def load_page(self, page_hash: str) -> str:
        path = self._path_for(page_hash)
        if not path.exists():
            raise FileNotFoundError(f"Page body not found: {path}")
        return path.read_text(encoding="utf-8")

    def exists(self, page_hash: str) -> bool:
        return self._path_for(page_hash).exists()

    def delete(self, page_hash: str) -> None:
        path = self._path_for(page_hash)
        if path.exists():
            path.unlink()
