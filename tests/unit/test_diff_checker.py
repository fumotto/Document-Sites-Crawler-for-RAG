from datetime import datetime, timezone

from src.app.crawler.diff_checker import DiffChecker, DiffDecision
from src.app.models.config_record import ConfigRecord
from src.app.models.crawl_result import CrawlResult
from src.app.models.manifest_record import ManifestRecord


def _config(mode="incremental"):
    return ConfigRecord(url="https://example.com", mode=mode)


def _manifest_record(etag=None, last_modified=None, sitemap_lastmod=None, content_sha256="sha"):
    return ManifestRecord(
        page_hash="hash1", etag=etag, last_modified=last_modified, sitemap_lastmod=sitemap_lastmod,
        content_sha256=content_sha256, last_crawled=datetime(2026, 1, 1, tzinfo=timezone.utc),
        crawl_result=CrawlResult.SUCCESS,
    )


def test_mode_full_always_fetches_unconditionally():
    # TestID: DIFF-001
    checker = DiffChecker()
    existing = _manifest_record(etag="e1", sitemap_lastmod="2026-01-01")

    outcome = checker.decide(existing, sitemap_lastmod="2026-01-01", config=_config(mode="full"))

    assert outcome.decision == DiffDecision.FETCH_UNCONDITIONAL


def test_new_url_with_no_existing_record_fetches_unconditionally():
    # TestID: DIFF-002
    checker = DiffChecker()

    outcome = checker.decide(existing=None, sitemap_lastmod=None, config=_config())

    assert outcome.decision == DiffDecision.FETCH_UNCONDITIONAL


def test_matching_sitemap_lastmod_skips_fetch():
    # TestID: DIFF-003
    checker = DiffChecker()
    existing = _manifest_record(sitemap_lastmod="2026-01-01")

    outcome = checker.decide(existing, sitemap_lastmod="2026-01-01", config=_config())

    assert outcome.decision == DiffDecision.SKIP_BY_SITEMAP_LASTMOD


def test_etag_present_with_mismatched_sitemap_lastmod_fetches_conditionally():
    # TestID: DIFF-004
    checker = DiffChecker()
    existing = _manifest_record(etag="e1", sitemap_lastmod="2026-01-01")

    outcome = checker.decide(existing, sitemap_lastmod="2026-02-01", config=_config())

    assert outcome.decision == DiffDecision.FETCH_CONDITIONAL


def test_no_etag_no_last_modified_no_sitemap_lastmod_fetches_unconditionally():
    # TestID: DIFF-005
    checker = DiffChecker()
    existing = _manifest_record(etag=None, last_modified=None, sitemap_lastmod=None)

    outcome = checker.decide(existing, sitemap_lastmod=None, config=_config())

    assert outcome.decision == DiffDecision.FETCH_UNCONDITIONAL


def test_content_changed_true_when_sha256_differs():
    # TestID: DIFF-006
    existing = _manifest_record(content_sha256="old-sha")

    assert DiffChecker.content_changed("new-sha", existing) is True


def test_content_changed_false_when_sha256_matches():
    # TestID: DIFF-007
    existing = _manifest_record(content_sha256="same-sha")

    assert DiffChecker.content_changed("same-sha", existing) is False


def test_content_changed_true_when_existing_is_none():
    # TestID: DIFF-008
    assert DiffChecker.content_changed("any-sha", existing=None) is True
