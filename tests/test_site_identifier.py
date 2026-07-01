import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.app.utils.site_identifier import generate_site_identifier


def test_lowercase_and_symbol_replacement():
    assert generate_site_identifier("https://supabase.com/docs/") == "supabase_com_docs"


def test_trailing_slash_equivalence():
    a = generate_site_identifier("https://example.com/docs/")
    b = generate_site_identifier("https://example.com/docs")
    assert a == b == "example_com_docs"


def test_case_insensitivity():
    a = generate_site_identifier("https://Supabase.com/Docs/")
    b = generate_site_identifier("https://supabase.com/docs/")
    assert a == b


def test_react_dev_example():
    assert generate_site_identifier("https://react.dev") == "react_dev"


def test_empty_url_raises():
    with pytest.raises(ValueError):
        generate_site_identifier("")
