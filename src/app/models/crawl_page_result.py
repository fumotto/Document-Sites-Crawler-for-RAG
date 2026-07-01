"""クロール結果を表す一時オブジェクト（06_処理シーケンス.md 1.1節）。

永続化されない。CrawlerService 内部でのみ使用し、crawl_result == SUCCESS の場合に
限り PageRepository（本文）・PageMetadataRepository（メタデータ）への書き込みが
行われる。crawl_result の値に関わらず ManifestRepository へはマージ更新ルール
（05_データ構造設計.md）に従って反映される。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.app.models.crawl_result import CrawlResult
from src.app.models.stats_record import StatsRecord


@dataclass(frozen=True)
class CrawlPageResult:
    url: str
    page_hash: str
    crawl_result: CrawlResult
    etag: Optional[str]
    last_modified: Optional[str]
    sitemap_lastmod: Optional[str]
    body_markdown: Optional[str]
    title: Optional[str]
    language: Optional[str]
    content_type: Optional[str]
    stats: Optional[StatsRecord]
    content_sha256: Optional[str]
    retrieved_at: datetime
