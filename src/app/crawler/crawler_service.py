"""CrawlerService（04_モジュール設計.md / 06_処理シーケンス.md 1,3,4,6節）。

サイト単位のクロールを統括する。sitemap利用時はsitemap記載URLを全件処理
（MAX_PAGES超過は警告のみ）、sitemap不在時は同一ドメインのフォールバック
クロール（MAX_PAGESをソフトリミットとして打ち切り）を行う。

すべて逐次処理（並列化しない）。REQUEST_DELAYで待機する。
"""
from __future__ import annotations

import logging
import httpx
from bs4 import BeautifulSoup
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlsplit

from src.app.crawler.diff_checker import DiffChecker, DiffDecision
from src.app.crawler.html_fetcher import HtmlFetcher
from src.app.crawler.markdown_extractor import MarkdownExtractor
from src.app.crawler.robots_parser import RobotsParser
from src.app.crawler.sitemap_fetcher import SitemapFetcher
from src.app.crawler.statistics_calculator import StatisticsCalculator
from src.app.crawler.url_filter import is_included
from src.app.exceptions.errors import CrawlError
from src.app.models.config_record import ConfigRecord
from src.app.models.crawl_page_result import CrawlPageResult
from src.app.models.crawl_result import CrawlResult
from src.app.models.manifest_record import ManifestRecord
from src.app.repository.manifest_repository import ManifestRepository
from src.app.repository.page_metadata_repository import PageMetadataRepository
from src.app.repository.page_repository import PageRepository
from src.app.utils.url_normalizer import compute_page_hash, normalize_url

logger = logging.getLogger(__name__)

_RETRYABLE_LOG_LEVEL = {
    "NETWORK_ERROR": logging.ERROR,
    "TIMEOUT": logging.ERROR,
    "SERVER_ERROR": logging.ERROR,
    "TOO_MANY_REQUESTS": logging.WARNING,
    "NOT_FOUND": logging.WARNING,
    "ROBOTS_DENIED": logging.WARNING,
}


@dataclass
class CrawlSiteOutcome:
    page_results: List[CrawlPageResult]
    discovery_complete: bool
    fatal_error: bool


class CrawlerService:
    def __init__(
        self,
        manifest_repo: ManifestRepository,
        page_repo: PageRepository,
        metadata_repo: PageMetadataRepository,
        config: ConfigRecord,
        session: Optional[httpx.Client] = None,
    ):
        self._manifest_repo = manifest_repo
        self._page_repo = page_repo
        self._metadata_repo = metadata_repo
        self._config = config
        self._session = session or httpx.Client()

        self._robots_parser = RobotsParser(config.user_agent, config.timeout_seconds, self._session)
        self._sitemap_fetcher = SitemapFetcher(config.user_agent, config.timeout_seconds, self._session)
        self._html_fetcher = HtmlFetcher(config.user_agent, config.timeout_seconds, self._session)
        self._extractor = MarkdownExtractor()
        self._stats_calculator = StatisticsCalculator()
        self._diff_checker = DiffChecker()

    def process_site(self, base_url: str) -> CrawlSiteOutcome:
        # Issue #6対応: INCLUDE未設定の場合、指定URLのパス部分を暗黙のスコープとして
        # 適用する。sitemapは常にドメインルートの /sitemap.xml を読みに行くため
        # （SitemapFetcher参照）、これを行わないと「https://example.com/docs/guides」
        # のようにパスを含むURLを指定しても、INCLUDE/EXCLUDEで絞り込まない限り
        # ドメイン全体（/blog/ 等）がクロール対象になってしまう。
        effective_include = self._resolve_effective_include(base_url)

        robots, robots_sitemaps = self._robots_parser.parse(base_url)
        sitemap_entries = self._sitemap_fetcher.fetch(base_url, robots_sitemaps)

        existing_manifest = self._manifest_repo.load()
        results: List[CrawlPageResult] = []
        discovered_urls: set = set()

        if sitemap_entries:
            discovery_complete = True  # sitemapは全件処理するため常にTrue（06節設計方針）

            if len(sitemap_entries) > self._config.max_pages:
                logger.warning(
                    "MAX_PAGES(%s) exceeded by sitemap entry count(%s). "
                    "All sitemap pages will still be processed.",
                    self._config.max_pages, len(sitemap_entries),
                )

            for entry in sitemap_entries:
                normalized = normalize_url(entry.url)
                if not is_included(normalized, effective_include, self._config.exclude):
                    continue
                if not RobotsParser.is_allowed(robots, self._config.user_agent, normalized):
                    self._record_and_log(existing_manifest, normalized, CrawlResult.ROBOTS_DENIED)
                    discovered_urls.add(normalized)
                    continue

                discovered_urls.add(normalized)
                result, _links = self._crawl_one(normalized, existing_manifest, entry.lastmod)
                if result is not None:
                    results.append(result)
                time.sleep(self._config.request_delay)
        else:
            discovery_complete = self._crawl_fallback(
                base_url, robots, existing_manifest, discovered_urls, results, effective_include
            )

        fatal_error = len(results) > 0 and all(
            r.crawl_result != CrawlResult.SUCCESS for r in results
        )
        # sitemap/フォールバックいずれでも1件もURLが見つからなかった場合も致命的失敗として扱う
        if not discovered_urls:
            fatal_error = True

        self._apply_deletion_guard(existing_manifest, discovered_urls, discovery_complete, effective_include)

        return CrawlSiteOutcome(
            page_results=results, discovery_complete=discovery_complete, fatal_error=fatal_error
        )

    @staticmethod
    def _resolve_include_from_path(base_url: str) -> List[str]:
        parsed = urlsplit(base_url)
        if parsed.path and parsed.path != "/":
            return [parsed.path]
        return []

    def _resolve_effective_include(self, base_url: str) -> List[str]:
        """Issue #6対応: INCLUDE未設定時、base_urlのパス部分を暗黙のINCLUDEとする。

        ユーザーが詳細設定でINCLUDEを明示的に指定している場合は、その指定を
        常に優先する（既存のCLI利用者の挙動を変えないため）。
        """
        if self._config.include:
            return self._config.include
        return self._resolve_include_from_path(base_url)

    # --- フォールバッククロール（06_処理シーケンス.md 4節） -------------------

    def _crawl_fallback(
        self, base_url, robots, existing_manifest, discovered_urls, results, effective_include,
    ) -> bool:
        base_domain = urlsplit(base_url).netloc
        visited: set = set()
        queue = deque([base_url])
        discovery_complete = True

        while queue:
            if len(visited) >= self._config.max_pages:
                logger.warning(
                    "MAX_PAGES(%s) reached during fallback crawl. Crawl truncated.",
                    self._config.max_pages,
                )
                discovery_complete = False
                break

            url = queue.popleft()
            normalized = normalize_url(url)
            if normalized in visited:
                continue
            visited.add(normalized)  # リクエスト開始時点で登録（二重リクエスト防止）

            if not is_included(normalized, effective_include, self._config.exclude):
                continue
            if not RobotsParser.is_allowed(robots, self._config.user_agent, normalized):
                self._record_and_log(existing_manifest, normalized, CrawlResult.ROBOTS_DENIED)
                discovered_urls.add(normalized)
                continue

            discovered_urls.add(normalized)
            result, links = self._crawl_one(normalized, existing_manifest, sitemap_lastmod=None, extract_links=True)
            if result is not None:
                results.append(result)

            for link in links:
                if urlsplit(link).netloc == base_domain:
                    queue.append(link)

            time.sleep(self._config.request_delay)

        return discovery_complete

    @staticmethod
    def _extract_links_from_html(base_url: str, html: str) -> List[str]:
        """生HTMLから同一ドメイン内リンクを抽出する（要件12節: 抽出済みMarkdownにはリンクを
        含めない設計のため、リンク抽出はクロール時取得の生HTMLから行う）。"""
        links: List[str] = []
        try:
            soup = BeautifulSoup(html, "lxml")
            for a_tag in soup.find_all("a", href=True):
                href_value = a_tag.get("href")
                if isinstance(href_value, (list, tuple)):
                    href_value = href_value[0] if href_value else ""
                href = str(href_value).strip()
                if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
                    continue
                links.append(urljoin(base_url, href))
        except Exception:
            pass
        return links

    # --- 1ページのクロール処理（sitemap/フォールバック共通） -------------------

    def _crawl_one(
        self, normalized_url: str, existing_manifest: Dict[str, ManifestRecord],
        sitemap_lastmod: Optional[str], extract_links: bool = False,
    ) -> tuple:
        """1ページをクロールする。(CrawlPageResult | None, List[str] links) を返す。

        links は extract_links=True かつ 200 OK で取得できた場合のみ非空になる
        （フォールバッククロール時のリンク発見に使用する）。
        """
        page_hash = compute_page_hash(normalized_url)
        existing = existing_manifest.get(normalized_url)

        outcome = self._diff_checker.decide(existing, sitemap_lastmod, self._config)
        if outcome.decision == DiffDecision.SKIP_BY_SITEMAP_LASTMOD:
            # HTTPリクエストを省略。manifest書き込みなし（05節: NOT_MODIFIEDと同様の扱い）
            return None, []

        etag = existing.etag if (existing and outcome.decision == DiffDecision.FETCH_CONDITIONAL) else None
        last_modified = (
            existing.last_modified if (existing and outcome.decision == DiffDecision.FETCH_CONDITIONAL) else None
        )

        try:
            response = self._html_fetcher.fetch(normalized_url, etag=etag, last_modified=last_modified)
        except CrawlError as exc:
            from src.app.exceptions.errors import CRAWL_EXCEPTION_TO_RESULT_VALUE

            result_value = CRAWL_EXCEPTION_TO_RESULT_VALUE.get(type(exc), "NETWORK_ERROR")
            crawl_result = CrawlResult(result_value)
            self._record_and_log(existing_manifest, normalized_url, crawl_result, message=str(exc))
            return CrawlPageResult(
                url=normalized_url, page_hash=page_hash, crawl_result=crawl_result,
                etag=None, last_modified=None, sitemap_lastmod=sitemap_lastmod,
                body_markdown=None, title=None, language=None, content_type=None,
                stats=None, content_sha256=None, retrieved_at=datetime.now(timezone.utc),
            ), []

        if response.status_code == 304:
            # manifest書き込みなし（05節）
            return CrawlPageResult(
                url=normalized_url, page_hash=page_hash, crawl_result=CrawlResult.NOT_MODIFIED,
                etag=response.etag, last_modified=response.last_modified, sitemap_lastmod=sitemap_lastmod,
                body_markdown=None, title=None, language=None, content_type=None,
                stats=None, content_sha256=None, retrieved_at=datetime.now(timezone.utc),
            ), []

        extraction = self._extractor.extract(response.text or "", normalized_url)
        body_markdown = extraction.body_markdown or ""
        stats = self._stats_calculator.calculate(body_markdown)

        import hashlib

        content_sha256 = hashlib.sha256(body_markdown.encode("utf-8")).hexdigest()
        retrieved_at = datetime.now(timezone.utc)

        manifest_record = ManifestRecord(
            page_hash=page_hash, etag=response.etag, last_modified=response.last_modified,
            sitemap_lastmod=sitemap_lastmod, content_sha256=content_sha256,
            last_crawled=retrieved_at, crawl_result=CrawlResult.SUCCESS,
        )
        self._manifest_repo.merge_update(normalized_url, manifest_record)

        self._page_repo.save(page_hash, body_markdown)
        from src.app.models.page_metadata_record import PageMetadataRecord

        self._metadata_repo.save(
            page_hash,
            PageMetadataRecord(
                title=extraction.title, url=normalized_url, language=extraction.language,
                word_count=stats.word_count, char_count=stats.char_count, token_count=stats.token_count,
                content_sha256=content_sha256, retrieved_at=retrieved_at,
                content_type=response.content_type or "text/html",
            ),
        )
        logger.info("Downloaded %s (sha256=%s)", normalized_url, content_sha256[:12])

        links: List[str] = []
        if extract_links and response.text:
            links = self._extract_links_from_html(response.url, response.text)

        return CrawlPageResult(
            url=normalized_url, page_hash=page_hash, crawl_result=CrawlResult.SUCCESS,
            etag=response.etag, last_modified=response.last_modified, sitemap_lastmod=sitemap_lastmod,
            body_markdown=body_markdown, title=extraction.title, language=extraction.language,
            content_type=response.content_type, stats=stats, content_sha256=content_sha256,
            retrieved_at=retrieved_at,
        ), links

    def _record_and_log(
        self, existing_manifest: Dict[str, ManifestRecord], url: str,
        crawl_result: CrawlResult, message: str = "",
    ) -> None:
        level = _RETRYABLE_LOG_LEVEL.get(crawl_result.value, logging.WARNING)
        logger.log(level, "%s %s %s", crawl_result.value, url, message)
        page_hash = compute_page_hash(url)
        record = ManifestRecord(
            page_hash=page_hash, etag=None, last_modified=None, sitemap_lastmod=None,
            content_sha256=None, last_crawled=datetime.now(timezone.utc), crawl_result=crawl_result,
        )
        self._manifest_repo.merge_update(url, record)

    def _apply_deletion_guard(
        self, existing_manifest: Dict[str, ManifestRecord], discovered_urls: set,
        discovery_complete: bool, effective_include: List[str],
    ) -> None:
        """削除ページ判定（06_処理シーケンス.md 8節）。

        探索が網羅的に完了した場合のみ削除判定を実行する。
        Issue #6対応: 比較範囲も effective_include（暗黙のパススコープ含む）に揃える。
        """
        if not discovery_complete:
            logger.warning("探索が完了していないため削除判定をスキップしました。")
            return

        target = {
            url for url in existing_manifest.keys()
            if is_included(url, effective_include, self._config.exclude)
        }
        deletion_candidates = target - discovered_urls
        if deletion_candidates:
            self._manifest_repo.delete_many(deletion_candidates)
            for url in deletion_candidates:
                logger.info("Deleted: %s", url)
