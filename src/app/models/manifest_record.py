"""manifest.json の1ページレコード（05_データ構造設計.md）。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.app.models.crawl_result import CrawlResult


@dataclass(frozen=True)
class ManifestRecord:
    page_hash: str
    etag: Optional[str]
    last_modified: Optional[str]
    sitemap_lastmod: Optional[str]
    content_sha256: Optional[str]
    last_crawled: datetime              # ISO8601 タイムゾーン付き
    crawl_result: CrawlResult
