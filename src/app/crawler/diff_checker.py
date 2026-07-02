"""DiffChecker（要件定義書20節）。

差分判定を3段階の優先順位で行う:
    1. sitemap lastmod比較（sitemapに記載があり、前回記録と一致すればHTTPリクエスト自体を省略）
    2. HTTP 304判定（ETag/Last-Modifiedによる条件付きリクエスト）
    3. 本文SHA256比較（200 OKで取得した本文が前回と同一かどうか）

sitemap lastmod一致時にHTTPリクエストを省略した場合、および304を受け取った場合は
manifest.jsonへの書き込みを行わない（05_データ構造設計.md / 06_処理シーケンス.md 設計方針）。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.app.models.config_record import ConfigRecord
from src.app.models.manifest_record import ManifestRecord


class DiffDecision(Enum):
    SKIP_BY_SITEMAP_LASTMOD = "SKIP_BY_SITEMAP_LASTMOD"   # HTTPリクエスト自体を省略
    FETCH_CONDITIONAL = "FETCH_CONDITIONAL"                 # ETag/Last-Modified付きで取得
    FETCH_UNCONDITIONAL = "FETCH_UNCONDITIONAL"             # 無条件で取得（新規URL等）


@dataclass
class DiffCheckOutcome:
    decision: DiffDecision


class DiffChecker:
    def decide(
        self,
        existing: Optional[ManifestRecord],
        sitemap_lastmod: Optional[str],
        config: ConfigRecord,
    ) -> DiffCheckOutcome:
        """クロール前の差分判定（1段階目・2段階目の入口）を行う。

        MODE=full の場合は常に無条件取得とする（要件19節）。
        """
        if config.mode == "full":
            return DiffCheckOutcome(decision=DiffDecision.FETCH_UNCONDITIONAL)

        if existing is None:
            return DiffCheckOutcome(decision=DiffDecision.FETCH_UNCONDITIONAL)

        # 1段階目: sitemap lastmod比較
        if sitemap_lastmod and existing.sitemap_lastmod and sitemap_lastmod == existing.sitemap_lastmod:
            return DiffCheckOutcome(decision=DiffDecision.SKIP_BY_SITEMAP_LASTMOD)

        # 2段階目: ETag/Last-Modifiedがあれば条件付きリクエストへ（304判定はHtmlFetcher/CrawlerServiceが処理）
        if existing.etag or existing.last_modified:
            return DiffCheckOutcome(decision=DiffDecision.FETCH_CONDITIONAL)

        return DiffCheckOutcome(decision=DiffDecision.FETCH_UNCONDITIONAL)

    @staticmethod
    def content_changed(new_sha256: str, existing: Optional[ManifestRecord]) -> bool:
        """3段階目: 本文SHA256比較。既存レコードがない、またはSHA256が異なればTrue。"""
        if existing is None or existing.content_sha256 is None:
            return True
        return new_sha256 != existing.content_sha256
