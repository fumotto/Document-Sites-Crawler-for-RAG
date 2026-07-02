"""ビルド結果DTO（06_処理シーケンス.md 1.1節）。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class BuildResultRecord:
    site_identifier: str
    total_pages_included: int
    duplicate_excluded_count: int
    chunk_file_count: int
    total_word_count: int
    warnings: List[str] = field(default_factory=list)
    has_fatal_error: bool = False
    archive_path: Optional[str] = None
