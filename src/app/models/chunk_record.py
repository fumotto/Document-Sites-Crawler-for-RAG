"""chunk_manifest.json の1件（05_データ構造設計.md）。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkRecord:
    title: str
    url: str
    file: str
    sha256: str
    word_count: int
