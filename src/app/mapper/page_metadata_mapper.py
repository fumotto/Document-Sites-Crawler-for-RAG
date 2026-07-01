"""PageMetadataRecord と metadata/{page_hash}.json の相互変換（05_データ構造設計.md）。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from src.app.models.page_metadata_record import PageMetadataRecord


def page_metadata_to_dict(record: PageMetadataRecord) -> Dict[str, Any]:
    return {
        "title": record.title,
        "url": record.url,
        "language": record.language,
        "word_count": record.word_count,
        "char_count": record.char_count,
        "token_count": record.token_count,
        "content_sha256": record.content_sha256,
        "retrieved_at": record.retrieved_at.isoformat(),
        "content_type": record.content_type,
    }


def dict_to_page_metadata(data: Dict[str, Any]) -> PageMetadataRecord:
    return PageMetadataRecord(
        title=data.get("title"),
        url=data["url"],
        language=data.get("language"),
        word_count=data["word_count"],
        char_count=data["char_count"],
        token_count=data["token_count"],
        content_sha256=data["content_sha256"],
        retrieved_at=datetime.fromisoformat(data["retrieved_at"]),
        content_type=data["content_type"],
    )
