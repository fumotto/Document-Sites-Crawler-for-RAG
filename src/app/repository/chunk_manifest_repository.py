"""ChunkManifestRepository（04_モジュール設計.md 4節 / 05_データ構造設計.md）。

output/{site}/chunk_manifest.json の読み書きを担当する。
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from src.app.mapper.chunk_mapper import chunk_records_to_list, list_to_chunk_records
from src.app.models.chunk_record import ChunkRecord
from src.app.utils.atomic_io import atomic_write_json, read_json


class ChunkManifestRepository:
    def __init__(self, output_dir: Path):
        self._path = output_dir / "chunk_manifest.json"

    def save(self, records: List[ChunkRecord]) -> None:
        atomic_write_json(self._path, chunk_records_to_list(records))

    def load(self) -> List[ChunkRecord]:
        if not self._path.exists():
            return []
        return list_to_chunk_records(read_json(self._path))
