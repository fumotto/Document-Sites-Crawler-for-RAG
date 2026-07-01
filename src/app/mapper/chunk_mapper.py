"""ChunkRecord と chunk_manifest.json の相互変換（05_データ構造設計.md）。"""
from __future__ import annotations

from typing import Any, Dict, List

from src.app.models.chunk_record import ChunkRecord


def chunk_record_to_dict(record: ChunkRecord) -> Dict[str, Any]:
    return {
        "title": record.title,
        "url": record.url,
        "file": record.file,
        "sha256": record.sha256,
        "word_count": record.word_count,
    }


def dict_to_chunk_record(data: Dict[str, Any]) -> ChunkRecord:
    return ChunkRecord(
        title=data["title"],
        url=data["url"],
        file=data["file"],
        sha256=data["sha256"],
        word_count=data["word_count"],
    )


def chunk_records_to_list(records: List[ChunkRecord]) -> List[Dict[str, Any]]:
    return [chunk_record_to_dict(r) for r in records]


def list_to_chunk_records(data: List[Dict[str, Any]]) -> List[ChunkRecord]:
    return [dict_to_chunk_record(d) for d in data]
