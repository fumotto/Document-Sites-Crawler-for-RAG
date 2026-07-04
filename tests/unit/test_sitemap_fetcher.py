from unittest.mock import MagicMock, patch

import httpx

from src.app.crawler.sitemap_fetcher import SitemapFetcher

URLSET_XML = b"""<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/a</loc></url>
  <url><loc>https://example.com/b</loc></url>
</urlset>"""

URLSET_WITH_LASTMOD_XML = b"""<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/a</loc><lastmod>2026-01-01T00:00:00+00:00</lastmod></url>
</urlset>"""

SITEMAP_INDEX_XML = b"""<?xml version="1.0"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.com/sub-sitemap.xml</loc></sitemap>
</sitemapindex>"""

INVALID_XML = b"<not-a-sitemap>plain text</not-a-sitemap>"


def _fake_get_factory(responses: dict):
    def fake_get(self, url, timeout=None, headers=None):
        resp = MagicMock()
        if url in responses:
            resp.status_code = 200
            resp.content = responses[url]
        else:
            resp.status_code = 404
            resp.content = b""
        return resp
    return fake_get


def test_urlset_returns_all_urls():
    # TestID: SM-001
    responses = {"https://example.com/sitemap.xml": URLSET_XML}
    with patch.object(httpx.Client, "get", _fake_get_factory(responses)):
        fetcher = SitemapFetcher("agent", 10)
        entries = fetcher.fetch("https://example.com")

    urls = {e.url for e in entries}
    assert urls == {"https://example.com/a", "https://example.com/b"}


def test_lastmod_extracted_correctly():
    # TestID: SM-002
    responses = {"https://example.com/sitemap.xml": URLSET_WITH_LASTMOD_XML}
    with patch.object(httpx.Client, "get", _fake_get_factory(responses)):
        fetcher = SitemapFetcher("agent", 10)
        entries = fetcher.fetch("https://example.com")

    assert len(entries) == 1
    assert entries[0].lastmod == "2026-01-01T00:00:00+00:00"


def test_sitemap_index_recursively_expanded():
    # TestID: SM-003
    responses = {
        "https://example.com/sitemap.xml": SITEMAP_INDEX_XML,
        "https://example.com/sub-sitemap.xml": URLSET_XML,
    }
    with patch.object(httpx.Client, "get", _fake_get_factory(responses)):
        fetcher = SitemapFetcher("agent", 10)
        entries = fetcher.fetch("https://example.com")

    urls = {e.url for e in entries}
    assert urls == {"https://example.com/a", "https://example.com/b"}


def test_recursion_depth_limit_stops_deep_nesting():
    # TestID: SM-004
    # Build a chain of sitemap indexes deeper than MAX_SITEMAP_DEPTH (5).
    responses = {}
    depth = 8
    for i in range(depth):
        next_url = f"https://example.com/level{i + 1}.xml"
        responses[f"https://example.com/level{i}.xml"] = (
            f'<?xml version="1.0"?><sitemapindex '
            f'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f'<sitemap><loc>{next_url}</loc></sitemap></sitemapindex>'
        ).encode("utf-8")
    responses[f"https://example.com/level{depth}.xml"] = URLSET_XML
    responses["https://example.com/sitemap.xml"] = responses["https://example.com/level0.xml"]

    with patch.object(httpx.Client, "get", _fake_get_factory(responses)):
        fetcher = SitemapFetcher("agent", 10)
        entries = fetcher.fetch("https://example.com")

    # The final urlset lives beyond MAX_SITEMAP_DEPTH, so it should not be reached.
    assert entries == []


def test_self_referencing_sitemap_index_does_not_infinite_loop():
    # TestID: SM-005
    self_ref_xml = (
        b'<?xml version="1.0"?><sitemapindex '
        b'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        b'<sitemap><loc>https://example.com/sitemap.xml</loc></sitemap>'
        b'</sitemapindex>'
    )
    responses = {"https://example.com/sitemap.xml": self_ref_xml}

    with patch.object(httpx.Client, "get", _fake_get_factory(responses)):
        fetcher = SitemapFetcher("agent", 10)
        entries = fetcher.fetch("https://example.com")  # should return, not hang

    assert entries == []


def test_fetch_failure_returns_empty_list():
    # TestID: SM-006
    with patch.object(httpx.Client, "get", _fake_get_factory({})):
        fetcher = SitemapFetcher("agent", 10)
        entries = fetcher.fetch("https://example.com")

    assert entries == []


def test_malformed_xml_returns_empty_list():
    # TestID: SM-007
    responses = {"https://example.com/sitemap.xml": b"<not valid xml"}
    with patch.object(httpx.Client, "get", _fake_get_factory(responses)):
        fetcher = SitemapFetcher("agent", 10)
        entries = fetcher.fetch("https://example.com")

    assert entries == []


def test_robots_txt_sitemap_urls_are_merged():
    # TestID: SM-008
    robots_sitemap_xml = b"""<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/from-robots</loc></url>
</urlset>"""
    responses = {
        "https://example.com/robots-sitemap.xml": robots_sitemap_xml,
        "https://example.com/sitemap.xml": URLSET_XML,
    }
    with patch.object(httpx.Client, "get", _fake_get_factory(responses)):
        fetcher = SitemapFetcher("agent", 10)
        entries = fetcher.fetch(
            "https://example.com",
            extra_sitemap_urls=["https://example.com/robots-sitemap.xml"],
        )

    urls = {e.url for e in entries}
    assert "https://example.com/from-robots" in urls
    assert "https://example.com/a" in urls


def test_duplicate_urls_across_sitemaps_deduplicated():
    # TestID: SM-009
    dup_xml = b"""<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/a</loc></url>
</urlset>"""
    responses = {
        "https://example.com/extra.xml": dup_xml,
        "https://example.com/sitemap.xml": URLSET_XML,
    }
    with patch.object(httpx.Client, "get", _fake_get_factory(responses)):
        fetcher = SitemapFetcher("agent", 10)
        entries = fetcher.fetch(
            "https://example.com", extra_sitemap_urls=["https://example.com/extra.xml"],
        )

    matching = [e for e in entries if e.url == "https://example.com/a"]
    assert len(matching) == 1


def test_unrecognized_root_element_returns_empty_list():
    # TestID: SM-010
    responses = {"https://example.com/sitemap.xml": INVALID_XML}
    with patch.object(httpx.Client, "get", _fake_get_factory(responses)):
        fetcher = SitemapFetcher("agent", 10)
        entries = fetcher.fetch("https://example.com")

    assert entries == []
