from datetime import datetime, timezone

from src.app.builder.page_ordering import order_pages
from src.app.models.page_metadata_record import PageMetadataRecord


def _meta(url):
    return PageMetadataRecord(
        title=None, url=url, language="en", word_count=10, char_count=50,
        token_count=10, content_sha256="sha", retrieved_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        content_type="text/html",
    )


def test_no_sitemap_order_sorts_by_url():
    # TestID: ORD-001
    pages = [("h1", _meta("https://e.com/c")), ("h2", _meta("https://e.com/a")), ("h3", _meta("https://e.com/b"))]

    result = order_pages(pages, sitemap_order=None)

    assert [r[1].url for r in result] == [
        "https://e.com/a", "https://e.com/b", "https://e.com/c",
    ]


def test_sitemap_order_takes_priority():
    # TestID: ORD-002
    pages = [("h1", _meta("https://e.com/b")), ("h2", _meta("https://e.com/a"))]
    sitemap_order = ["https://e.com/b", "https://e.com/a"]

    result = order_pages(pages, sitemap_order=sitemap_order)

    assert [r[1].url for r in result] == ["https://e.com/b", "https://e.com/a"]


def test_pages_not_in_sitemap_appear_after_sitemap_pages_in_url_order():
    # TestID: ORD-003
    pages = [
        ("h1", _meta("https://e.com/sitemap-page")),
        ("h2", _meta("https://e.com/z-not-in-sitemap")),
        ("h3", _meta("https://e.com/a-not-in-sitemap")),
    ]
    sitemap_order = ["https://e.com/sitemap-page"]

    result = order_pages(pages, sitemap_order=sitemap_order)

    urls = [r[1].url for r in result]
    assert urls[0] == "https://e.com/sitemap-page"
    assert urls[1:] == ["https://e.com/a-not-in-sitemap", "https://e.com/z-not-in-sitemap"]


def test_sort_key_structure_unlisted_pages_share_common_index():
    # TestID: ORD-004
    pages = [
        ("h1", _meta("https://e.com/z")),
        ("h2", _meta("https://e.com/y")),
        ("h3", _meta("https://e.com/x")),
    ]
    sitemap_order = ["https://e.com/only-listed"]

    result = order_pages(pages, sitemap_order=sitemap_order)

    # None of these pages are in sitemap_order, so they all fall back to the
    # same order_index value (len(sitemap_order)) and are then sorted by URL.
    urls = [r[1].url for r in result]
    assert urls == ["https://e.com/x", "https://e.com/y", "https://e.com/z"]
