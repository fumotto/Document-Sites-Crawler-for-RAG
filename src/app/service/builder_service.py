"""BuilderService（04_モジュール設計.md / 06_処理シーケンス.md 5節）。

キャッシュ全件から成果物（docs_XXX.md / Index.md / chunk_manifest.json）を
再構築する。差分更新の有無に関わらず、常に全件から再構築する（要件15節）。
"""
from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from src.app.builder.chunk_builder import ChunkBuilder
from src.app.builder.duplicate_resolver import DuplicateResolver
from src.app.builder.index_builder import IndexBuilder
from src.app.builder.page_ordering import order_pages
from src.app.exceptions.errors import BuilderError
from src.app.models.build_result_record import BuildResultRecord
from src.app.models.page_metadata_record import PageMetadataRecord
from src.app.models.site_context_record import SiteContextRecord
from src.app.repository.chunk_manifest_repository import ChunkManifestRepository
from src.app.repository.page_metadata_repository import PageMetadataRepository
from src.app.repository.page_repository import PageRepository
from src.app.utils.atomic_io import atomic_write_text

logger = logging.getLogger(__name__)


class BuilderService:
    def __init__(self):
        self._duplicate_resolver = DuplicateResolver()
        self._chunk_builder = ChunkBuilder()
        self._index_builder = IndexBuilder()

    def build(
        self, site_context: SiteContextRecord, sitemap_order: Optional[List[str]] = None,
    ) -> BuildResultRecord:
        metadata_repo = PageMetadataRepository(site_context.metadata_dir)
        page_repo = PageRepository(site_context.pages_dir)
        chunk_manifest_repo = ChunkManifestRepository(site_context.output_dir)

        warnings: List[str] = []

        # crawl_result=SUCCESS のページ全件を読み込む
        all_metadata: List[Tuple[str, PageMetadataRecord]] = metadata_repo.load_all()

        if not all_metadata:
            logger.warning("No pages available to build for site: %s", site_context.site_identifier)
            return BuildResultRecord(
                site_identifier=site_context.site_identifier, total_pages_included=0,
                duplicate_excluded_count=0, chunk_file_count=0, total_word_count=0,
                warnings=["No pages available to build."], has_fatal_error=False, archive_path=None,
            )

        # 重複判定
        resolution = self._duplicate_resolver.resolve(all_metadata)

        # 並び替え（ChunkBuilder/IndexBuilder共通ロジック）
        ordered = order_pages(resolution.canonical, sitemap_order)

        # 本文読み込み（見つからない場合は処理を中断する。要件15節）
        page_bodies = {}
        for page_hash, _record in ordered:
            try:
                page_bodies[page_hash] = page_repo.load_page(page_hash)
            except FileNotFoundError as exc:
                logger.error("Page body not found for build: %s", page_hash)
                raise BuilderError(str(exc)) from exc

        # チャンク生成
        chunk_result = self._chunk_builder.build_chunks(ordered, page_bodies, site_context.config.word_limit)
        warnings.extend(chunk_result.warnings)

        for chunk_file in chunk_result.files:
            atomic_write_text(site_context.output_dir / chunk_file.filename, chunk_file.content)

        chunk_manifest_repo.save(chunk_result.chunk_records)

        # Index.md生成
        index_content = self._index_builder.build_index(ordered, page_bodies, site_context.site_identifier)
        atomic_write_text(site_context.output_dir / "Index.md", index_content)

        total_word_count = sum(record.word_count for _hash, record in ordered)

        logger.info(
            "Build complete for %s: %s pages included, %s duplicates excluded, %s chunk files.",
            site_context.site_identifier, len(ordered), len(resolution.excluded), len(chunk_result.files),
        )

        return BuildResultRecord(
            site_identifier=site_context.site_identifier,
            total_pages_included=len(ordered),
            duplicate_excluded_count=len(resolution.excluded),
            chunk_file_count=len(chunk_result.files),
            total_word_count=total_word_count,
            warnings=warnings,
            has_fatal_error=False,
            archive_path=None,
        )
