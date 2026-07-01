"""ページ並び替え共通ロジック（06_処理シーケンス.md 設計方針 SEQ-10）。

ChunkBuilder と IndexBuilder で共通の並び替えロジックを使用する。
sitemap順を優先し、sitemapに記載のないページはURL順とする。
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from src.app.models.page_metadata_record import PageMetadataRecord


def order_pages(
    pages: List[Tuple[str, PageMetadataRecord]],
    sitemap_order: Optional[List[str]] = None,
) -> List[Tuple[str, PageMetadataRecord]]:
    """(page_hash, PageMetadataRecord) のリストを並び替える。

    Args:
        pages: 並び替え対象
        sitemap_order: sitemap記載順の正規化済みURLリスト（存在すれば優先）
    """
    if sitemap_order:
        order_index = {url: i for i, url in enumerate(sitemap_order)}
        return sorted(
            pages,
            key=lambda item: (order_index.get(item[1].url, len(sitemap_order)), item[1].url),
        )
    return sorted(pages, key=lambda item: item[1].url)
