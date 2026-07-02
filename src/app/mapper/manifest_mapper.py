"""ManifestRecord と manifest.json の相互変換（05_データ構造設計.md）。

Mapper以外はJSONを直接操作しない、という設計方針に基づき、日時フィールドの
ISO8601（タイムゾーン付き）シリアライズ／デシリアライズもここに集約する。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from src.app.models.crawl_result import CrawlResult
from src.app.models.manifest_record import ManifestRecord

MANIFEST_VERSION = "1"


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat()


def _deserialize_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def manifest_record_to_dict(record: ManifestRecord) -> Dict[str, Any]:
    return {
        "page_hash": record.page_hash,
        "etag": record.etag,
        "last_modified": record.last_modified,
        "sitemap_lastmod": record.sitemap_lastmod,
        "content_sha256": record.content_sha256,
        "last_crawled": _serialize_datetime(record.last_crawled),
        "crawl_result": record.crawl_result.value,
    }


def dict_to_manifest_record(data: Dict[str, Any]) -> ManifestRecord:
    return ManifestRecord(
        page_hash=data["page_hash"],
        etag=data.get("etag"),
        last_modified=data.get("last_modified"),
        sitemap_lastmod=data.get("sitemap_lastmod"),
        content_sha256=data.get("content_sha256"),
        last_crawled=_deserialize_datetime(data["last_crawled"]),
        crawl_result=CrawlResult(data["crawl_result"]),
    )


def manifest_dict_to_document(pages: Dict[str, ManifestRecord]) -> Dict[str, Any]:
    """{normalized_url: ManifestRecord} → manifest.json全体の辞書表現。"""
    return {
        "version": MANIFEST_VERSION,
        "pages": {url: manifest_record_to_dict(rec) for url, rec in pages.items()},
    }


def document_to_manifest_dict(document: Dict[str, Any]) -> Dict[str, ManifestRecord]:
    """manifest.json全体の辞書表現 → {normalized_url: ManifestRecord}。"""
    pages = document.get("pages", {})
    return {url: dict_to_manifest_record(entry) for url, entry in pages.items()}
