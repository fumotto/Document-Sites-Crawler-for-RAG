from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.app.crawler.crawler_service import CrawlerService
from src.app.models.config_record import ConfigRecord
from src.app.models.crawl_result import CrawlResult
from src.app.models.manifest_record import ManifestRecord
from src.app.repository.manifest_repository import ManifestRepository
from src.app.repository.page_metadata_repository import PageMetadataRepository
from src.app.repository.page_repository import PageRepository

SITEMAP_XML = b"""<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/a</loc></url>
  <url><loc>https://example.com/b</loc></url>
</urlset>"""


def _make_config(**overrides):
    base = dict(
        url="https://example.com", base_urls=[], manifest_path_override=None,
        mode="incremental", word_limit=450000, request_delay=0, user_agent="test-agent",
        include=[], exclude=[], max_pages=1000, timeout_seconds=10,
    )
    base.update(overrides)
    return ConfigRecord(**base)


def _make_service(tmp_path, config):
    manifest_repo = ManifestRepository(tmp_path / "manifest.json")
    page_repo = PageRepository(tmp_path / "pages")
    meta_repo = PageMetadataRepository(tmp_path / "metadata")
    service = CrawlerService(manifest_repo, page_repo, meta_repo, config)
    return service, manifest_repo, page_repo, meta_repo


def _robots_ok(url):
    return url.endswith("robots.txt")


def test_sitemap_all_entries_crawled(tmp_path):
    # TestID: CS-001
    pages = {
        "https://example.com/a": "<html><head><title>A</title></head><body><p>page a body content here</p></body></html>",
        "https://example.com/b": "<html><head><title>B</title></head><body><p>page b body content here</p></body></html>",
    }

    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        resp = MagicMock()
        if _robots_ok(url):
            resp.status_code = 200
            resp.text = "User-agent: *\nAllow: /\n"
            return resp
        if url.endswith("sitemap.xml"):
            resp.status_code = 200
            resp.content = SITEMAP_XML
            return resp
        if url in pages:
            resp.status_code = 200
            resp.headers = {"Content-Type": "text/html"}
            resp.text = pages[url]
            return resp
        resp.status_code = 404
        resp.headers = {}
        return resp

    config = _make_config()
    service, *_ = _make_service(tmp_path, config)

    with patch.object(httpx.Client, "get", fake_get):
        outcome = service.process_site("https://example.com")

    crawled = {r.url for r in outcome.page_results}
    assert crawled == {"https://example.com/a", "https://example.com/b"}


def test_no_sitemap_falls_back_to_link_crawling(tmp_path):
    # TestID: CS-002
    index_html = (
        "<html><head><title>Index</title></head><body>"
        "<p>Home body content.</p>"
        '<a href="/child">child</a>'
        "</body></html>"
    )
    child_html = "<html><head><title>Child</title></head><body><p>Child body content.</p></body></html>"

    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        resp = MagicMock()
        if _robots_ok(url):
            resp.status_code = 200
            resp.text = "User-agent: *\nAllow: /\n"
            return resp
        if url.endswith("sitemap.xml"):
            resp.status_code = 404
            resp.content = b""
            return resp
        if url == "https://example.com/":
            resp.status_code = 200
            resp.headers = {"Content-Type": "text/html"}
            resp.text = index_html
            return resp
        if url == "https://example.com/child":
            resp.status_code = 200
            resp.headers = {"Content-Type": "text/html"}
            resp.text = child_html
            return resp
        resp.status_code = 404
        resp.headers = {}
        return resp

    config = _make_config(url="https://example.com/")
    service, *_ = _make_service(tmp_path, config)

    with patch.object(httpx.Client, "get", fake_get):
        outcome = service.process_site("https://example.com/")

    crawled = {r.url for r in outcome.page_results}
    assert "https://example.com/child" in crawled


def test_robots_disallowed_url_recorded_and_not_crawled(tmp_path):
    # TestID: CS-003
    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        resp = MagicMock()
        if _robots_ok(url):
            resp.status_code = 200
            resp.text = "User-agent: *\nDisallow: /b\n"
            return resp
        if url.endswith("sitemap.xml"):
            resp.status_code = 200
            resp.content = SITEMAP_XML
            return resp
        # /a would be reachable, but the test only cares that /b is denied.
        resp.status_code = 200
        resp.headers = {"Content-Type": "text/html"}
        resp.text = "<html><head><title>A</title></head><body><p>a body content</p></body></html>"
        return resp

    config = _make_config()
    service, manifest_repo, page_repo, _meta_repo = _make_service(tmp_path, config)

    with patch.object(httpx.Client, "get", fake_get):
        service.process_site("https://example.com")

    manifest = manifest_repo.load()
    assert manifest["https://example.com/b"].crawl_result == CrawlResult.ROBOTS_DENIED
    # No page body should exist for the denied URL.
    from src.app.utils.url_normalizer import compute_page_hash
    denied_hash = compute_page_hash("https://example.com/b")
    assert page_repo.exists(denied_hash) is False


def test_all_pages_failing_marks_fatal_error(tmp_path):
    # TestID: CS-004
    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        resp = MagicMock()
        if _robots_ok(url):
            resp.status_code = 200
            resp.text = "User-agent: *\nAllow: /\n"
            return resp
        if url.endswith("sitemap.xml"):
            resp.status_code = 200
            resp.content = SITEMAP_XML
            return resp
        resp.status_code = 404
        resp.headers = {}
        return resp

    config = _make_config()
    service, *_ = _make_service(tmp_path, config)

    with patch.object(httpx.Client, "get", fake_get):
        outcome = service.process_site("https://example.com")

    assert outcome.fatal_error is True


def test_no_urls_discovered_marks_fatal_error(tmp_path):
    # TestID: CS-005
    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        resp = MagicMock()
        if _robots_ok(url):
            resp.status_code = 200
            resp.text = "User-agent: *\nAllow: /\n"
            return resp
        # sitemap missing AND fallback root page itself 404s -> nothing discovered
        resp.status_code = 404
        resp.headers = {}
        resp.content = b""
        return resp

    config = _make_config(url="https://example.com/")
    service, *_ = _make_service(tmp_path, config)

    with patch.object(httpx.Client, "get", fake_get):
        outcome = service.process_site("https://example.com/")

    assert outcome.fatal_error is True


def test_max_pages_exceeded_via_sitemap_still_processes_all(tmp_path):
    # TestID: CS-006
    many_urls_xml = b"""<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/1</loc></url>
  <url><loc>https://example.com/2</loc></url>
  <url><loc>https://example.com/3</loc></url>
</urlset>"""

    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        resp = MagicMock()
        if _robots_ok(url):
            resp.status_code = 200
            resp.text = "User-agent: *\nAllow: /\n"
            return resp
        if url.endswith("sitemap.xml"):
            resp.status_code = 200
            resp.content = many_urls_xml
            return resp
        resp.status_code = 200
        resp.headers = {"Content-Type": "text/html"}
        resp.text = "<html><head><title>P</title></head><body><p>content</p></body></html>"
        return resp

    config = _make_config(max_pages=2)  # smaller than the 3 sitemap URLs
    service, *_ = _make_service(tmp_path, config)

    with patch.object(httpx.Client, "get", fake_get):
        outcome = service.process_site("https://example.com")

    # All 3 URLs still processed despite MAX_PAGES=2 (sitemap mode never truncates).
    assert len(outcome.page_results) == 3


def test_max_pages_reached_truncates_fallback_crawl(tmp_path):
    # TestID: CS-007
    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        resp = MagicMock()
        if _robots_ok(url):
            resp.status_code = 200
            resp.text = "User-agent: *\nAllow: /\n"
            return resp
        if url.endswith("sitemap.xml"):
            resp.status_code = 404
            resp.content = b""
            return resp
        # Every page links to a new unique child so the fallback crawl queue
        # never runs dry on its own; MAX_PAGES must be what stops it.
        page_num = url.rstrip("/").split("/")[-1] or "root"
        next_num = 0
        try:
            next_num = int(page_num) + 1
        except ValueError:
            next_num = 1
        html = (
            f"<html><head><title>P{page_num}</title></head><body>"
            f"<p>content for page {page_num}</p>"
            f'<a href="/{next_num}">next</a>'
            "</body></html>"
        )
        resp.status_code = 200
        resp.headers = {"Content-Type": "text/html"}
        resp.text = html
        return resp

    config = _make_config(url="https://example.com/", max_pages=2)
    service, *_ = _make_service(tmp_path, config)

    with patch.object(httpx.Client, "get", fake_get):
        outcome = service.process_site("https://example.com/")

    assert outcome.discovery_complete is False


def test_discovery_incomplete_skips_deletion_guard(tmp_path):
    # TestID: CS-008
    manifest_repo = ManifestRepository(tmp_path / "manifest.json")
    manifest_repo.merge_update(
        "https://example.com/stale",
        ManifestRecord(
            page_hash="staleHash", etag=None, last_modified=None, sitemap_lastmod=None,
            content_sha256="sha", last_crawled=datetime.now(timezone.utc),
            crawl_result=CrawlResult.SUCCESS,
        ),
    )

    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        resp = MagicMock()
        if _robots_ok(url):
            resp.status_code = 200
            resp.text = "User-agent: *\nAllow: /\n"
            return resp
        if url.endswith("sitemap.xml"):
            resp.status_code = 404
            resp.content = b""
            return resp
        html = '<html><head><title>Root</title></head><body><p>content</p><a href="/next">n</a></body></html>'
        resp.status_code = 200
        resp.headers = {"Content-Type": "text/html"}
        resp.text = html
        return resp

    config = _make_config(url="https://example.com/", max_pages=1)
    page_repo = PageRepository(tmp_path / "pages")
    meta_repo = PageMetadataRepository(tmp_path / "metadata")
    service = CrawlerService(manifest_repo, page_repo, meta_repo, config)

    with patch.object(httpx.Client, "get", fake_get):
        service.process_site("https://example.com/")

    manifest = manifest_repo.load()
    assert "https://example.com/stale" in manifest


def test_discovery_complete_deletes_undiscovered_url(tmp_path):
    # TestID: CS-009
    manifest_repo = ManifestRepository(tmp_path / "manifest.json")
    manifest_repo.merge_update(
        "https://example.com/gone",
        ManifestRecord(
            page_hash="goneHash", etag=None, last_modified=None, sitemap_lastmod=None,
            content_sha256="sha", last_crawled=datetime.now(timezone.utc),
            crawl_result=CrawlResult.SUCCESS,
        ),
    )

    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        resp = MagicMock()
        if _robots_ok(url):
            resp.status_code = 200
            resp.text = "User-agent: *\nAllow: /\n"
            return resp
        if url.endswith("sitemap.xml"):
            resp.status_code = 200
            resp.content = SITEMAP_XML  # only /a and /b, not /gone
            return resp
        resp.status_code = 200
        resp.headers = {"Content-Type": "text/html"}
        resp.text = "<html><head><title>P</title></head><body><p>content</p></body></html>"
        return resp

    config = _make_config()
    page_repo = PageRepository(tmp_path / "pages")
    meta_repo = PageMetadataRepository(tmp_path / "metadata")
    service = CrawlerService(manifest_repo, page_repo, meta_repo, config)

    with patch.object(httpx.Client, "get", fake_get):
        service.process_site("https://example.com")

    manifest = manifest_repo.load()
    assert "https://example.com/gone" not in manifest


def test_200_ok_saved_to_all_three_repositories(tmp_path):
    # TestID: CS-010
    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        resp = MagicMock()
        if _robots_ok(url):
            resp.status_code = 200
            resp.text = "User-agent: *\nAllow: /\n"
            return resp
        if url.endswith("sitemap.xml"):
            resp.status_code = 200
            resp.content = SITEMAP_XML
            return resp
        resp.status_code = 200
        resp.headers = {"Content-Type": "text/html"}
        resp.text = "<html><head><title>P</title></head><body><p>content here</p></body></html>"
        return resp

    config = _make_config()
    service, manifest_repo, page_repo, meta_repo = _make_service(tmp_path, config)

    with patch.object(httpx.Client, "get", fake_get):
        service.process_site("https://example.com")

    manifest = manifest_repo.load()
    assert manifest["https://example.com/a"].crawl_result == CrawlResult.SUCCESS
    all_meta = meta_repo.load_all()
    page_hash = manifest["https://example.com/a"].page_hash
    assert any(h == page_hash for h, _r in all_meta)
    assert page_repo.exists(page_hash) is True


def test_304_not_modified_does_not_update_manifest(tmp_path):
    # TestID: CS-011
    manifest_repo = ManifestRepository(tmp_path / "manifest.json")
    manifest_repo.merge_update(
        "https://example.com/a",
        ManifestRecord(
            page_hash="hashA", etag='"etag1"', last_modified=None, sitemap_lastmod=None,
            content_sha256="sha-original", last_crawled=datetime(2020, 1, 1, tzinfo=timezone.utc),
            crawl_result=CrawlResult.SUCCESS,
        ),
    )

    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        resp = MagicMock()
        if _robots_ok(url):
            resp.status_code = 200
            resp.text = "User-agent: *\nAllow: /\n"
            return resp
        if url.endswith("sitemap.xml"):
            resp.status_code = 200
            resp.content = b"""<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/a</loc></url>
</urlset>"""
            return resp
        if url == "https://example.com/a":
            resp.status_code = 304
            resp.headers = {"ETag": '"etag1"'}
            resp.text = None
            return resp
        resp.status_code = 404
        resp.headers = {}
        return resp

    page_repo = PageRepository(tmp_path / "pages")
    meta_repo = PageMetadataRepository(tmp_path / "metadata")
    config = _make_config()
    service = CrawlerService(manifest_repo, page_repo, meta_repo, config)

    with patch.object(httpx.Client, "get", fake_get):
        service.process_site("https://example.com")

    manifest = manifest_repo.load()
    assert manifest["https://example.com/a"].last_crawled == datetime(2020, 1, 1, tzinfo=timezone.utc)


def test_sitemap_lastmod_match_skips_http_fetch_entirely(tmp_path):
    # TestID: CS-012
    manifest_repo = ManifestRepository(tmp_path / "manifest.json")
    manifest_repo.merge_update(
        "https://example.com/a",
        ManifestRecord(
            page_hash="hashA", etag=None, last_modified=None, sitemap_lastmod="2026-01-01",
            content_sha256="sha", last_crawled=datetime(2020, 1, 1, tzinfo=timezone.utc),
            crawl_result=CrawlResult.SUCCESS,
        ),
    )

    fetch_calls = []

    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        resp = MagicMock()
        if _robots_ok(url):
            resp.status_code = 200
            resp.text = "User-agent: *\nAllow: /\n"
            return resp
        if url.endswith("sitemap.xml"):
            resp.status_code = 200
            resp.content = b"""<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/a</loc><lastmod>2026-01-01</lastmod></url>
</urlset>"""
            return resp
        fetch_calls.append(url)
        resp.status_code = 200
        resp.headers = {"Content-Type": "text/html"}
        resp.text = "<html><head><title>P</title></head><body><p>content</p></body></html>"
        return resp

    page_repo = PageRepository(tmp_path / "pages")
    meta_repo = PageMetadataRepository(tmp_path / "metadata")
    config = _make_config()
    service = CrawlerService(manifest_repo, page_repo, meta_repo, config)

    with patch.object(httpx.Client, "get", fake_get):
        service.process_site("https://example.com")

    assert "https://example.com/a" not in fetch_calls


def test_crawl_one_skip_by_sitemap_lastmod_returns_none_and_no_result(tmp_path):
    # TestID: CS-013
    manifest_repo = ManifestRepository(tmp_path / "manifest.json")
    existing_manifest = {
        "https://example.com/a": ManifestRecord(
            page_hash="hashA", etag=None, last_modified=None, sitemap_lastmod="2026-01-01",
            content_sha256="sha", last_crawled=datetime(2020, 1, 1, tzinfo=timezone.utc),
            crawl_result=CrawlResult.SUCCESS,
        )
    }
    page_repo = PageRepository(tmp_path / "pages")
    meta_repo = PageMetadataRepository(tmp_path / "metadata")
    config = _make_config()
    service = CrawlerService(manifest_repo, page_repo, meta_repo, config)

    result, links = service._crawl_one(
        "https://example.com/a", existing_manifest, sitemap_lastmod="2026-01-01",
    )

    assert result is None
    assert links == []


def test_fallback_crawl_ignores_external_domain_links(tmp_path):
    # TestID: CS-014
    index_html = (
        "<html><head><title>Index</title></head><body>"
        "<p>Home body content.</p>"
        '<a href="https://external-site.com/page">external</a>'
        "</body></html>"
    )

    seen_urls = []

    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        seen_urls.append(url)
        resp = MagicMock()
        if _robots_ok(url):
            resp.status_code = 200
            resp.text = "User-agent: *\nAllow: /\n"
            return resp
        if url.endswith("sitemap.xml"):
            resp.status_code = 404
            resp.content = b""
            return resp
        if url == "https://example.com/":
            resp.status_code = 200
            resp.headers = {"Content-Type": "text/html"}
            resp.text = index_html
            return resp
        resp.status_code = 404
        resp.headers = {}
        return resp

    config = _make_config(url="https://example.com/")
    service, *_ = _make_service(tmp_path, config)

    with patch.object(httpx.Client, "get", fake_get):
        service.process_site("https://example.com/")

    assert not any("external-site.com" in u for u in seen_urls)


def test_deletion_guard_respects_current_include_exclude_filter(tmp_path):
    # TestID: CS-015
    manifest_repo = ManifestRepository(tmp_path / "manifest.json")
    now = datetime.now(timezone.utc)
    # In-filter-scope but not discovered this time -> should be deleted.
    manifest_repo.merge_update(
        "https://example.com/docs/old",
        ManifestRecord(
            page_hash="h1", etag=None, last_modified=None, sitemap_lastmod=None,
            content_sha256="sha", last_crawled=now, crawl_result=CrawlResult.SUCCESS,
        ),
    )
    # Out-of-filter-scope (not under /docs) -> should NOT be touched even
    # though it's also not discovered this run.
    manifest_repo.merge_update(
        "https://example.com/blog/untouched",
        ManifestRecord(
            page_hash="h2", etag=None, last_modified=None, sitemap_lastmod=None,
            content_sha256="sha", last_crawled=now, crawl_result=CrawlResult.SUCCESS,
        ),
    )

    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        resp = MagicMock()
        if _robots_ok(url):
            resp.status_code = 200
            resp.text = "User-agent: *\nAllow: /\n"
            return resp
        if url.endswith("sitemap.xml"):
            resp.status_code = 200
            resp.content = b"""<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/docs/new</loc></url>
</urlset>"""
            return resp
        resp.status_code = 200
        resp.headers = {"Content-Type": "text/html"}
        resp.text = "<html><head><title>P</title></head><body><p>content</p></body></html>"
        return resp

    config = _make_config(include=["/docs"])
    page_repo = PageRepository(tmp_path / "pages")
    meta_repo = PageMetadataRepository(tmp_path / "metadata")
    service = CrawlerService(manifest_repo, page_repo, meta_repo, config)

    with patch.object(httpx.Client, "get", fake_get):
        service.process_site("https://example.com")

    manifest = manifest_repo.load()
    assert "https://example.com/docs/old" not in manifest
    assert "https://example.com/blog/untouched" in manifest
