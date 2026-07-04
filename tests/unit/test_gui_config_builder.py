import pytest

from src.app.exceptions.errors import ConfigError
from src.app.gui.config_builder import build_config_from_form


def _base_form(**overrides):
    form = {
        "urls_text": "https://example.com",
        "mode": "incremental",
        "word_limit": 450000,
        "request_delay": 0.5,
        "include": "",
        "exclude": "",
        "max_pages": 1000,
        "timeout_seconds": 30,
        "log_level": "INFO",
    }
    form.update(overrides)
    return form


def test_single_url_maps_to_url_field():
    # TestID: GCB-001
    config = build_config_from_form(_base_form())
    assert config.url == "https://example.com"
    assert config.base_urls == []


def test_multiple_urls_map_to_base_urls():
    # TestID: GCB-002
    form = _base_form(urls_text="https://a.com\nhttps://b.com")
    config = build_config_from_form(form)
    assert config.url is None
    assert config.base_urls == ["https://a.com", "https://b.com"]


def test_empty_urls_raises_config_error():
    # TestID: GCB-003
    with pytest.raises(ConfigError):
        build_config_from_form(_base_form(urls_text="   \n  "))


def test_invalid_url_scheme_raises_config_error():
    # TestID: GCB-004
    with pytest.raises(ConfigError):
        build_config_from_form(_base_form(urls_text="ftp://example.com"))


def test_invalid_mode_raises_config_error():
    # TestID: GCB-005
    with pytest.raises(ConfigError):
        build_config_from_form(_base_form(mode="bogus"))


def test_include_exclude_csv_parsing():
    # TestID: GCB-006
    form = _base_form(include="/docs, /guides", exclude="/blog")
    config = build_config_from_form(form)
    assert config.include == ["/docs", "/guides"]
    assert config.exclude == ["/blog"]


def test_manifest_override_always_none_for_gui():
    # TestID: GCB-007
    config = build_config_from_form(_base_form())
    assert config.manifest_path_override is None


def test_non_numeric_word_limit_raises_config_error():
    # TestID: GCB-008
    with pytest.raises(ConfigError):
        build_config_from_form(_base_form(word_limit="abc"))


def test_invalid_log_level_raises_config_error():
    # TestID: GCB-009
    with pytest.raises(ConfigError):
        build_config_from_form(_base_form(log_level="TRACE"))


def test_one_invalid_url_among_multiple_lines_raises_config_error():
    # TestID: GCB-010
    form = _base_form(urls_text="https://a.com\nftp://b.com")
    with pytest.raises(ConfigError):
        build_config_from_form(form)
