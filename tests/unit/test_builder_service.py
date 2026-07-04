from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.app.exceptions.errors import BuilderError
from src.app.models.config_record import ConfigRecord
from src.app.models.page_metadata_record import PageMetadataRecord
from src.app.models.site_context_record import SiteContextRecord
from src.app.repository.page_metadata_repository import PageMetadataRepository
from src.app.repository.page_repository import PageRepository
from src.app.service.builder_service import BuilderService


def _config(**overrides):
    base = dict(
        url="https://example.com", base_urls=[], manifest_path_override=None,
        mode="incremental", word_limit=450000, request_delay=0, user_agent="test",
        include=[], exclude=[], max_pages=1000, timeout_seconds=10,
    )
    base.update(overrides)
    return ConfigRecord(**base)


def _site_context(tmp_path, config=None):
    config = config or _config()
    cache_dir = tmp_path / "cache" / "site"
    output_dir = tmp_path / "output" / "site"
    archive_dir = tmp_path / "archives" / "site"
    (cache_dir / "pages").mkdir(parents=True, exist_ok=True)
    (cache_dir / "metadata").mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    return SiteContextRecord(
        site_identifier="site", base_url="https://example.com", cache_dir=cache_dir,
        output_dir=output_dir, archive_dir=archive_dir,
        manifest_path=cache_dir / "manifest.json", config=config,
        started_at=datetime.now(timezone.utc),
    )


def _meta(url, word_count=10, sha256="sha", title="T"):
    return PageMetadataRecord(
        title=title, url=url, language="en", word_count=word_count, char_count=word_count * 5,
        token_count=word_count, content_sha256=sha256,
        retrieved_at=datetime.now(timezone.utc), content_type="text/html",
    )


def test_no_metadata_returns_empty_result_without_fatal_error(tmp_path):
    # TestID: BS-001
    ctx = _site_context(tmp_path)
    service = BuilderService()

    result = service.build(ctx)

    assert result.total_pages_included == 0
    assert result.has_fatal_error is False
    assert result.warnings


def test_full_build_generates_expected_output_files(tmp_path):
    # TestID: BS-002
    ctx = _site_context(tmp_path)
    meta_repo = PageMetadataRepository(ctx.metadata_dir)
    page_repo = PageRepository(ctx.pages_dir)

    meta_repo.save("hash1", _meta("https://example.com/a"))
    meta_repo.save("hash2", _meta("https://example.com/b", sha256="sha2"))
    page_repo.save("hash1", "Body A content.")
    page_repo.save("hash2", "Body B content.")

    service = BuilderService()
    result = service.build(ctx)

    assert result.total_pages_included == 2
    assert (ctx.output_dir / "docs_001.md").exists()
    assert (ctx.output_dir / "Index.md").exists()
    assert (ctx.output_dir / "chunk_manifest.json").exists()


def test_missing_page_body_raises_builder_error(tmp_path):
    # TestID: BS-003
    ctx = _site_context(tmp_path)
    meta_repo = PageMetadataRepository(ctx.metadata_dir)
    meta_repo.save("hash1", _meta("https://example.com/a"))
    # Intentionally do not save the page body.

    service = BuilderService()

    with pytest.raises(BuilderError):
        service.build(ctx)


def test_duplicate_pages_excluded_from_total_count(tmp_path):
    # TestID: BS-004
    ctx = _site_context(tmp_path)
    meta_repo = PageMetadataRepository(ctx.metadata_dir)
    page_repo = PageRepository(ctx.pages_dir)

    meta_repo.save("hash1", _meta("https://example.com/a", sha256="dup-sha"))
    meta_repo.save("hash2", _meta("https://example.com/b", sha256="dup-sha"))
    page_repo.save("hash1", "Same body.")
    page_repo.save("hash2", "Same body.")

    service = BuilderService()
    result = service.build(ctx)

    assert result.total_pages_included == 1
    assert result.duplicate_excluded_count == 1


def test_page_order_follows_sitemap_order_when_given(tmp_path):
    # TestID: BS-005
    ctx = _site_context(tmp_path)
    meta_repo = PageMetadataRepository(ctx.metadata_dir)
    page_repo = PageRepository(ctx.pages_dir)

    meta_repo.save("hashB", _meta("https://example.com/b", sha256="sha-b"))
    meta_repo.save("hashA", _meta("https://example.com/a", sha256="sha-a"))
    page_repo.save("hashB", "BODY_B_MARKER")
    page_repo.save("hashA", "BODY_A_MARKER")

    service = BuilderService()
    sitemap_order = ["https://example.com/b", "https://example.com/a"]
    service.build(ctx, sitemap_order=sitemap_order)

    content = (ctx.output_dir / "docs_001.md").read_text(encoding="utf-8")
    assert content.index("BODY_B_MARKER") < content.index("BODY_A_MARKER")
