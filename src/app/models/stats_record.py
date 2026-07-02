"""ページ統計情報DTO。

06_処理シーケンス.md の CrawlPageResult.stats フィールドで参照される型として、
本実装で新規に定義する（PageMetadataRecord の word_count/char_count/token_count
に対応する一時オブジェクト）。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StatsRecord:
    word_count: int
    char_count: int
    token_count: int
