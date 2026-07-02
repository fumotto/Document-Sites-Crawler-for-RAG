"""metadata/{page_hash}.json の1件（05_データ構造設計.md）。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class PageMetadataRecord:
    title: Optional[str]
    url: str
    language: Optional[str]
    word_count: int
    char_count: int
    token_count: int
    content_sha256: str
    retrieved_at: datetime              # ISO8601 タイムゾーン付き
    content_type: str
