from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.app.exceptions.errors import BuilderError, LockAcquisitionError
from src.app.models.build_result_record import BuildResultRecord
from src.app.models.config_record import ConfigRecord
from src.app.models.site_context_record import SiteContextRecord
from src.app.service.orchestrator import EXIT_FATAL, EXIT_PARTIAL_FAILURE, EXIT_SUCCESS, Orchestrator


def _build_result(site_identifier="site", has_fatal_error=False, total_pages_included=1):
    return BuildResultRecord(
        site_identifier=site_identifier, total_pages_included=total_pages_included,
        duplicate_excluded_count=0, chunk_file_count=1, total_word_count=100,
        warnings=[], has_fatal_error=has_fatal_error, archive_path=None,
    )


def test_all_sites_succeed_returns_exit_success():
    # TestID: ORC-001
    results = [_build_result(has_fatal_error=False), _build_result("site2", has_fatal_error=False)]
    assert Orchestrator._determine_exit_code(results) == EXIT_SUCCESS


def test_one_site_fatal_returns_exit_partial_failure():
    # TestID: ORC-002
    results = [_build_result(has_fatal_error=False), _build_result("site2", has_fatal_error=True)]
    assert Orchestrator._determine_exit_code(results) == EXIT_PARTIAL_FAILURE


def test_empty_site_results_returns_exit_fatal():
    # TestID: ORC-003
    assert Orchestrator._determine_exit_code([]) == EXIT_FATAL


def test_lock_failure_marks_site_fatal_but_continues_other_sites(tmp_path):
    # TestID: ORC-004
    orchestrator = Orchestrator()
    config = ConfigRecord(
        url=None, base_urls=["https://locked.com", "https://ok.com"],
        manifest_path_override=None, mode="incremental", word_limit=450000,
        request_delay=0, user_agent="test", include=[], exclude=[],
        max_pages=1000, timeout_seconds=10,
    )

    original_process_one_site = orchestrator._process_one_site

    def fake_process_one_site(site_context, cfg):
        if "locked" in site_context.base_url:
            raise LockAcquisitionError("locked")
        return _build_result(site_context.site_identifier, has_fatal_error=False)

    orchestrator._process_one_site = fake_process_one_site

    # site_lock is a real contextmanager; we need process_one_site to raise
    # LockAcquisitionError from *within* the `with site_lock(...)` block to
    # simulate the real failure path. Patch site_lock itself instead so the
    # raised error surfaces exactly as run() expects.
    import src.app.service.orchestrator as orch_module

    def fake_site_lock(lock_path):
        from contextlib import contextmanager

        @contextmanager
        def _cm():
            if "locked" in str(lock_path):
                raise LockAcquisitionError("locked")
            yield

        return _cm()

    orchestrator._process_one_site = original_process_one_site
    orch_module.site_lock = fake_site_lock

    # Stub crawler/builder/archive to avoid real network/filesystem crawling.
    orchestrator._builder_service.build = MagicMock(
        return_value=_build_result("ok_com", has_fatal_error=False)
    )
    orchestrator._archive_service.archive = MagicMock(return_value=None)

    import src.app.crawler.crawler_service as crawler_service_module

    class FakeCrawlerService:
        def __init__(self, *args, **kwargs):
            pass

        def process_site(self, base_url):
            from src.app.crawler.crawler_service import CrawlSiteOutcome
            return CrawlSiteOutcome(page_results=[], discovery_complete=True, fatal_error=False)

    orch_module.CrawlerService = FakeCrawlerService

    job_result = orchestrator.run(config, root=tmp_path)

    fatal_sites = [r for r in job_result.site_results if r.has_fatal_error]
    ok_sites = [r for r in job_result.site_results if not r.has_fatal_error]
    assert len(fatal_sites) == 1
    assert len(ok_sites) == 1
    assert job_result.exit_code == EXIT_PARTIAL_FAILURE


def test_crawl_fatal_but_cache_exists_still_runs_build_and_archive(tmp_path):
    # TestID: ORC-005
    orchestrator = Orchestrator()
    orchestrator._builder_service.build = MagicMock(
        return_value=_build_result("site", has_fatal_error=False, total_pages_included=3)
    )
    orchestrator._archive_service.archive = MagicMock(return_value="archive.zip")

    config = ConfigRecord(
        url="https://example.com", base_urls=[], manifest_path_override=None,
        mode="incremental", word_limit=450000, request_delay=0, user_agent="test",
        include=[], exclude=[], max_pages=1000, timeout_seconds=10,
    )
    site_context = SiteContextRecord(
        site_identifier="site", base_url="https://example.com",
        cache_dir=tmp_path / "cache" / "site", output_dir=tmp_path / "output" / "site",
        archive_dir=tmp_path / "archives" / "site",
        manifest_path=tmp_path / "cache" / "site" / "manifest.json",
        config=config, started_at=datetime.now(timezone.utc),
    )
    site_context.cache_dir.mkdir(parents=True, exist_ok=True)
    site_context.output_dir.mkdir(parents=True, exist_ok=True)
    site_context.archive_dir.mkdir(parents=True, exist_ok=True)

    import src.app.service.orchestrator as orch_module

    class FailingCrawlerService:
        def __init__(self, *args, **kwargs):
            pass

        def process_site(self, base_url):
            from src.app.crawler.crawler_service import CrawlSiteOutcome
            return CrawlSiteOutcome(page_results=[], discovery_complete=True, fatal_error=True)

    orch_module.CrawlerService = FailingCrawlerService

    result = orchestrator._process_one_site(site_context, config)

    orchestrator._builder_service.build.assert_called_once()
    orchestrator._archive_service.archive.assert_called_once()
    assert result.has_fatal_error is True  # because crawl_fatal was True


def test_zero_pages_built_skips_archive(tmp_path):
    # TestID: ORC-006
    orchestrator = Orchestrator()
    orchestrator._builder_service.build = MagicMock(
        return_value=_build_result("site", has_fatal_error=False, total_pages_included=0)
    )
    orchestrator._archive_service.archive = MagicMock(return_value="should-not-be-called.zip")

    config = ConfigRecord(
        url="https://example.com", base_urls=[], manifest_path_override=None,
        mode="incremental", word_limit=450000, request_delay=0, user_agent="test",
        include=[], exclude=[], max_pages=1000, timeout_seconds=10,
    )
    site_context = SiteContextRecord(
        site_identifier="site", base_url="https://example.com",
        cache_dir=tmp_path / "cache" / "site", output_dir=tmp_path / "output" / "site",
        archive_dir=tmp_path / "archives" / "site",
        manifest_path=tmp_path / "cache" / "site" / "manifest.json",
        config=config, started_at=datetime.now(timezone.utc),
    )
    site_context.cache_dir.mkdir(parents=True, exist_ok=True)
    site_context.output_dir.mkdir(parents=True, exist_ok=True)
    site_context.archive_dir.mkdir(parents=True, exist_ok=True)

    import src.app.service.orchestrator as orch_module

    class OkCrawlerService:
        def __init__(self, *args, **kwargs):
            pass

        def process_site(self, base_url):
            from src.app.crawler.crawler_service import CrawlSiteOutcome
            return CrawlSiteOutcome(page_results=[], discovery_complete=True, fatal_error=False)

    orch_module.CrawlerService = OkCrawlerService

    result = orchestrator._process_one_site(site_context, config)

    orchestrator._archive_service.archive.assert_not_called()
    assert result.archive_path is None


def test_builder_error_results_in_fatal_build_result(tmp_path):
    # TestID: ORC-007
    orchestrator = Orchestrator()
    orchestrator._builder_service.build = MagicMock(side_effect=BuilderError("body missing"))

    config = ConfigRecord(
        url="https://example.com", base_urls=[], manifest_path_override=None,
        mode="incremental", word_limit=450000, request_delay=0, user_agent="test",
        include=[], exclude=[], max_pages=1000, timeout_seconds=10,
    )
    site_context = SiteContextRecord(
        site_identifier="site", base_url="https://example.com",
        cache_dir=tmp_path / "cache" / "site", output_dir=tmp_path / "output" / "site",
        archive_dir=tmp_path / "archives" / "site",
        manifest_path=tmp_path / "cache" / "site" / "manifest.json",
        config=config, started_at=datetime.now(timezone.utc),
    )
    site_context.cache_dir.mkdir(parents=True, exist_ok=True)
    site_context.output_dir.mkdir(parents=True, exist_ok=True)
    site_context.archive_dir.mkdir(parents=True, exist_ok=True)

    import src.app.service.orchestrator as orch_module

    class OkCrawlerService:
        def __init__(self, *args, **kwargs):
            pass

        def process_site(self, base_url):
            from src.app.crawler.crawler_service import CrawlSiteOutcome
            return CrawlSiteOutcome(page_results=[], discovery_complete=True, fatal_error=False)

    orch_module.CrawlerService = OkCrawlerService

    result = orchestrator._process_one_site(site_context, config)

    assert result.has_fatal_error is True


def test_single_url_and_multi_base_urls_target_correct_sites(tmp_path):
    # TestID: ORC-008
    orchestrator = Orchestrator()
    orchestrator._process_one_site = MagicMock(
        side_effect=lambda ctx, cfg: _build_result(ctx.site_identifier, has_fatal_error=False)
    )

    single_config = ConfigRecord(
        url="https://single.com", base_urls=[], manifest_path_override=None,
        mode="incremental", word_limit=450000, request_delay=0, user_agent="test",
        include=[], exclude=[], max_pages=1000, timeout_seconds=10,
    )
    multi_config = ConfigRecord(
        url=None, base_urls=["https://a.com", "https://b.com"], manifest_path_override=None,
        mode="incremental", word_limit=450000, request_delay=0, user_agent="test",
        include=[], exclude=[], max_pages=1000, timeout_seconds=10,
    )

    single_result = orchestrator.run(single_config, root=tmp_path / "single")
    multi_result = orchestrator.run(multi_config, root=tmp_path / "multi")

    assert [r.site_identifier for r in single_result.site_results] == ["single_com"]
    assert {r.site_identifier for r in multi_result.site_results} == {"a_com", "b_com"}
