import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.app.utils.url_normalizer import compute_page_hash, normalize_url


def test_scheme_and_hostname_lowercased():
    # TestID: URLN-001
    result = normalize_url("HTTPS://Example.COM/Path")
    assert result == "https://example.com/Path"


def test_default_port_removed_https():
    # TestID: URLN-002
    result = normalize_url("https://example.com:443/a")
    assert result == "https://example.com/a"


def test_default_port_removed_http():
    # TestID: URLN-003
    result = normalize_url("http://example.com:80/a")
    assert result == "http://example.com/a"


def test_non_default_port_preserved():
    # TestID: URLN-004
    result = normalize_url("https://example.com:8443/a")
    assert result == "https://example.com:8443/a"


def test_fragment_removed():
    # TestID: URLN-005
    result = normalize_url("https://example.com/a#section1")
    assert "#" not in result
    assert result == "https://example.com/a"


def test_query_preserved():
    # TestID: URLN-006
    result = normalize_url("https://example.com/a?tab=2")
    assert result == "https://example.com/a?tab=2"


def test_missing_path_defaults_to_root():
    # TestID: URLN-007
    result = normalize_url("https://example.com")
    assert result == "https://example.com/"


def test_trailing_slash_is_not_normalized_away():
    # TestID: URLN-008
    with_slash = normalize_url("https://example.com/a/")
    without_slash = normalize_url("https://example.com/a")
    assert with_slash == "https://example.com/a/"
    assert without_slash == "https://example.com/a"
    assert with_slash != without_slash


def test_page_hash_is_deterministic():
    # TestID: URLN-009
    url = normalize_url("https://example.com/a")
    assert compute_page_hash(url) == compute_page_hash(url)


def test_page_hash_differs_for_different_urls():
    # TestID: URLN-010
    a = compute_page_hash(normalize_url("https://example.com/a"))
    b = compute_page_hash(normalize_url("https://example.com/b"))
    assert a != b
