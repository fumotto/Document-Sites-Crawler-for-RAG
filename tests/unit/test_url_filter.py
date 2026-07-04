from src.app.crawler.url_filter import is_included


def test_no_include_no_exclude_allows_all():
    # TestID: UF-001
    assert is_included("https://example.com/anything", [], []) is True


def test_include_prefix_match_allows():
    # TestID: UF-002
    assert is_included("https://example.com/docs/guide", ["/docs"], []) is True


def test_include_prefix_mismatch_excludes():
    # TestID: UF-003
    assert is_included("https://example.com/blog/x", ["/docs"], []) is False


def test_exclude_prefix_match_excludes():
    # TestID: UF-004
    assert is_included("https://example.com/blog/x", [], ["/blog"]) is False


def test_exclude_takes_priority_over_include():
    # TestID: UF-005
    result = is_included(
        "https://example.com/docs/internal/x", ["/docs"], ["/docs/internal"]
    )
    assert result is False


def test_any_of_multiple_include_patterns_matches():
    # TestID: UF-006
    result = is_included("https://example.com/guides/x", ["/docs", "/guides"], [])
    assert result is True


def test_prefix_match_causes_unintended_partial_match():
    # TestID: UF-007
    # "/docs" as a prefix also matches "/docsAndMore" due to plain startswith
    # semantics (no path-segment boundary check).
    result = is_included("https://example.com/docsAndMore/x", ["/docs"], [])
    assert result is True
