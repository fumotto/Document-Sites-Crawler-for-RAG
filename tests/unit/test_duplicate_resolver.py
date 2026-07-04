from datetime import datetime, timezone

from src.app.builder.duplicate_resolver import DuplicateResolver
from src.app.models.page_metadata_record import PageMetadataRecord


def _meta(url, sha256, retrieved_at):
    return PageMetadataRecord(
        title="T", url=url, language="en", word_count=10, char_count=50,
        token_count=12, content_sha256=sha256, retrieved_at=retrieved_at, content_type="text/html",
    )


def test_newest_retrieved_at_wins():
    # TestID: DUP-001
    resolver = DuplicateResolver()
    old = datetime(2020, 1, 1, tzinfo=timezone.utc)
    new = datetime(2026, 1, 1, tzinfo=timezone.utc)
    items = [
        ("hashA", _meta("https://example.com/a", "sha-dup", old)),
        ("hashB", _meta("https://example.com/b", "sha-dup", new)),
        ("hashC", _meta("https://example.com/c", "sha-unique", new)),
    ]
    result = resolver.resolve(items)
    canonical_urls = {r.url for _h, r in result.canonical}
    assert canonical_urls == {"https://example.com/b", "https://example.com/c"}
    assert len(result.excluded) == 1
    assert result.excluded[0][1].url == "https://example.com/a"


def test_all_unique_pages_remain_canonical():
    # TestID: DUP-002
    resolver = DuplicateResolver()
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    items = [
        ("h1", _meta("https://example.com/a", "sha-a", now)),
        ("h2", _meta("https://example.com/b", "sha-b", now)),
        ("h3", _meta("https://example.com/c", "sha-c", now)),
    ]
    result = resolver.resolve(items)
    assert len(result.canonical) == 3
    assert result.excluded == []


def test_excluded_pages_contain_older_duplicate_only():
    # TestID: DUP-003
    resolver = DuplicateResolver()
    old = datetime(2020, 1, 1, tzinfo=timezone.utc)
    new = datetime(2026, 1, 1, tzinfo=timezone.utc)
    items = [
        ("hashA", _meta("https://example.com/a", "sha-dup", old)),
        ("hashB", _meta("https://example.com/b", "sha-dup", new)),
    ]
    result = resolver.resolve(items)
    excluded_urls = {r.url for _h, r in result.excluded}
    assert excluded_urls == {"https://example.com/a"}


def test_three_or_more_duplicates_only_newest_kept():
    # TestID: DUP-004
    resolver = DuplicateResolver()
    t1 = datetime(2020, 1, 1, tzinfo=timezone.utc)
    t2 = datetime(2022, 1, 1, tzinfo=timezone.utc)
    t3 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    items = [
        ("h1", _meta("https://example.com/a", "sha-dup", t1)),
        ("h2", _meta("https://example.com/b", "sha-dup", t2)),
        ("h3", _meta("https://example.com/c", "sha-dup", t3)),
    ]
    result = resolver.resolve(items)
    assert len(result.canonical) == 1
    assert result.canonical[0][1].url == "https://example.com/c"
    assert len(result.excluded) == 2


def test_empty_input_returns_empty_result():
    # TestID: DUP-005
    resolver = DuplicateResolver()
    result = resolver.resolve([])
    assert result.canonical == []
    assert result.excluded == []


def test_same_retrieved_at_keeps_first_in_input_order():
    # TestID: DUP-006
    resolver = DuplicateResolver()
    same_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    items = [
        ("h1", _meta("https://example.com/first", "sha-dup", same_time)),
        ("h2", _meta("https://example.com/second", "sha-dup", same_time)),
    ]
    result = resolver.resolve(items)
    assert len(result.canonical) == 1
    # Python's sort is stable; reverse=True on equal keys preserves original
    # relative order, so the first input item remains first after reversal
    # is applied consistently by sorted().
    assert result.canonical[0][1].url == "https://example.com/first"
