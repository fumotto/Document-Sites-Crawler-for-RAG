import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

from src.app.utils.site_identifier import generate_site_identifier


def test_lowercase_and_symbol_replacement():
    # TestID: SID-001
    assert generate_site_identifier("https://supabase.com/docs/") == "supabase_com_docs"


def test_trailing_slash_equivalence():
    # TestID: SID-002
    a = generate_site_identifier("https://example.com/docs/")
    b = generate_site_identifier("https://example.com/docs")
    assert a == b == "example_com_docs"


def test_case_insensitivity():
    # TestID: SID-003
    a = generate_site_identifier("https://Supabase.com/Docs/")
    b = generate_site_identifier("https://supabase.com/docs/")
    assert a == b


def test_react_dev_example():
    # TestID: SID-004
    assert generate_site_identifier("https://react.dev") == "react_dev"


def test_empty_url_raises():
    # TestID: SID-005
    with pytest.raises(ValueError):
        generate_site_identifier("")


def test_repeated_symbols_collapse():
    # TestID: SID-006
    result = generate_site_identifier("https://example.com/a:::b")
    assert "___" not in result
    assert result == "example_com_a_b"


def test_double_slash_in_path_collapses():
    # TestID: SID-007
    result = generate_site_identifier("https://example.com/a//b")
    assert "__" not in result
    assert result == "example_com_a_b"


def test_http_and_https_are_equivalent():
    # TestID: SID-008
    a = generate_site_identifier("http://example.com/x")
    b = generate_site_identifier("https://example.com/x")
    assert a == b


def test_subdomain_and_port_are_converted():
    # TestID: SID-009
    result = generate_site_identifier("https://docs.example.com:8080/a")
    assert result == "docs_example_com_8080_a"
