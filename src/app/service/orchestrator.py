"""Orchestrator（04_モジュール設計.md / 06_処理シーケンス.md 2節 / 07_CLI仕様.md 6節）。

対象サイトごとに逐次処理（クロール→ビルド→アーカイブ）を行い、
最終的な終了コード（0/1/2）を判定する。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from src.app.archive.archive_service import ArchiveService
from src.app.crawler.crawler_service import CrawlerService
from src.app.exceptions.errors import BuilderError, LockAcquisitionError
from src.app.models.build_result_record import BuildResultRecord
from src.app.models.config_record import ConfigRecord
from src.app.repository.manifest_repository import ManifestRepository
from src.app.repository.page_metadata_repository import PageMetadataRepository
from src.app.repository.page_repository import PageRepository
from src.app.service.builder_service import BuilderService
from src.app.utils.directory_bootstrap import PROJECT_ROOT, build_site_context, ensure_project_directories
from src.app.utils.site_lock import site_lock

logger = logging.getLogger(__name__)

EXIT_SUCCESS = 0
EXIT_FATAL = 1
EXIT_PARTIAL_FAILURE = 2


@dataclass
class JobResult:
    site_results: List[BuildResultRecord]
    exit_code: int


class Orchestrator:
    def __init__(self):
        self._builder_service = BuilderService()
        self._archive_service = ArchiveService()

    def run(self, config: ConfigRecord, root: Optional[Path] = None) -> JobResult:
        """対象サイトを逐次処理する。

        Args:
            config: 実行時設定
            root: cache/output/archives/logs のルートディレクトリ。
                  省略時はカレントディレクトリ（CLI版・Docker版の既定動作、
                  03_ディレクトリ構成.md 準拠）。GUI版は
                  08_デスクトップアプリ化要件定義書.md 8節の
                  `%USERPROFILE%\\DocumentSitesCrawlerForRAG\\` を明示的に渡す。
        """
        effective_root = root if root is not None else PROJECT_ROOT
        ensure_project_directories(effective_root)

        target_urls = [config.url] if config.url else config.base_urls
        site_results: List[BuildResultRecord] = []

        for base_url in target_urls:
            site_context = build_site_context(base_url, config, root=effective_root)
            logger.info("=== Processing site: %s (%s) ===", base_url, site_context.site_identifier)

            try:
                with site_lock(site_context.lock_path):
                    result = self._process_one_site(site_context, config)
            except LockAcquisitionError as exc:
                logger.error(str(exc))
                result = BuildResultRecord(
                    site_identifier=site_context.site_identifier, total_pages_included=0,
                    duplicate_excluded_count=0, chunk_file_count=0, total_word_count=0,
                    warnings=[str(exc)], has_fatal_error=True, archive_path=None,
                )

            site_results.append(result)
            logger.info(
                "=== Site done: %s (fatal_error=%s, pages=%s) ===",
                site_context.site_identifier, result.has_fatal_error, result.total_pages_included,
            )

        exit_code = self._determine_exit_code(site_results)
        return JobResult(site_results=site_results, exit_code=exit_code)

    def _process_one_site(self, site_context, config: ConfigRecord) -> BuildResultRecord:
        manifest_repo = ManifestRepository(site_context.manifest_path)
        page_repo = PageRepository(site_context.pages_dir)
        metadata_repo = PageMetadataRepository(site_context.metadata_dir)

        crawler_service = CrawlerService(manifest_repo, page_repo, metadata_repo, config)

        crawl_fatal = False
        try:
            crawl_outcome = crawler_service.process_site(site_context.base_url)
            crawl_fatal = crawl_outcome.fatal_error
        except Exception:
            logger.exception("Unexpected error during crawl for %s", site_context.site_identifier)
            crawl_fatal = True

        # ビルド・アーカイブは、クロールが致命的失敗でもキャッシュが存在する限り必ず実行する
        # （06_処理シーケンス.md 設計方針: SEQ-6）
        try:
            build_result = self._builder_service.build(site_context)
        except BuilderError as exc:
            logger.error("Build failed for %s: %s", site_context.site_identifier, exc)
            return BuildResultRecord(
                site_identifier=site_context.site_identifier, total_pages_included=0,
                duplicate_excluded_count=0, chunk_file_count=0, total_word_count=0,
                warnings=[str(exc)], has_fatal_error=True, archive_path=None,
            )

        archive_path = None
        if build_result.total_pages_included > 0:
            try:
                archive_path = self._archive_service.archive(site_context)
            except Exception:
                logger.exception("Archive failed for %s", site_context.site_identifier)

        has_fatal_error = crawl_fatal or build_result.has_fatal_error

        return BuildResultRecord(
            site_identifier=build_result.site_identifier,
            total_pages_included=build_result.total_pages_included,
            duplicate_excluded_count=build_result.duplicate_excluded_count,
            chunk_file_count=build_result.chunk_file_count,
            total_word_count=build_result.total_word_count,
            warnings=build_result.warnings,
            has_fatal_error=has_fatal_error,
            archive_path=archive_path,
        )

    @staticmethod
    def _determine_exit_code(site_results: List[BuildResultRecord]) -> int:
        """07_CLI仕様.md 6節: 0=完全成功／1=致命的エラー（未実行）／2=部分的失敗"""
        if not site_results:
            return EXIT_FATAL
        if any(r.has_fatal_error for r in site_results):
            return EXIT_PARTIAL_FAILURE
        return EXIT_SUCCESS
