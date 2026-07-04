from datetime import datetime, timezone

from src.app.builder.index_builder import SUMMARY_CHAR_LIMIT, IndexBuilder
from src.app.models.page_metadata_record import PageMetadataRecord


def _meta(url, title=None):
    return PageMetadataRecord(
        title=title, url=url, language="en", word_count=10, char_count=50,
        token_count=10, content_sha256="sha", retrieved_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        content_type="text/html",
    )


def test_title_used_as_heading_when_present():
    # TestID: IDX-001
    builder = IndexBuilder()
    pages = [("h1", _meta("https://e.com/a", title="Authentication"))]

    result = builder.build_index(pages, {"h1": "body"}, "site")

    assert "## Authentication" in result


def test_url_used_as_heading_when_title_is_none():
    # TestID: IDX-002
    builder = IndexBuilder()
    pages = [("h1", _meta("https://e.com/a", title=None))]

    result = builder.build_index(pages, {"h1": "body"}, "site")

    assert "## https://e.com/a" in result


def test_summary_under_limit_shown_in_full():
    # TestID: IDX-003
    builder = IndexBuilder()
    pages = [("h1", _meta("https://e.com/a"))]
    short_body = "short body text"
    assert len(short_body) <= SUMMARY_CHAR_LIMIT

    result = builder.build_index(pages, {"h1": short_body}, "site")

    assert f"- Summary: {short_body}" in result


def test_summary_over_limit_truncated_with_ellipsis():
    # TestID: IDX-004
    builder = IndexBuilder()
    pages = [("h1", _meta("https://e.com/a"))]
    long_body = "x" * (SUMMARY_CHAR_LIMIT + 50)

    result = builder.build_index(pages, {"h1": long_body}, "site")

    expected_summary = "x" * SUMMARY_CHAR_LIMIT + "..."
    assert f"- Summary: {expected_summary}" in result


def test_empty_page_list_produces_header_only():
    # TestID: IDX-005
    builder = IndexBuilder()

    result = builder.build_index([], {}, "site")

    assert "# Index: site" in result
    assert "0 pages" in result
