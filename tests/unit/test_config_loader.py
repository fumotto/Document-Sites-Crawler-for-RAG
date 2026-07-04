import pytest

from src.app.config.config_loader import load_config
from src.app.exceptions.errors import ConfigError


def _base_env(**overrides):
    env = {"MAX_PAGES": "1000", "TIMEOUT_SECONDS": "30"}
    env.update(overrides)
    return env


def test_cli_url_confirms_single_site_processing():
    # TestID: CFG-001
    config = load_config(["https://a.com"], env=_base_env())
    assert config.url == "https://a.com"
    assert config.base_urls == []


def test_no_cli_url_with_base_urls_becomes_multi_site():
    # TestID: CFG-002
    config = load_config([], env=_base_env(BASE_URLS="https://a.com\nhttps://b.com"))
    assert config.url is None
    assert config.base_urls == ["https://a.com", "https://b.com"]


def test_no_url_and_no_base_urls_raises_config_error():
    # TestID: CFG-003
    with pytest.raises(ConfigError):
        load_config([], env=_base_env())


def test_manifest_without_url_raises_config_error():
    # TestID: CFG-004
    with pytest.raises(ConfigError):
        load_config(["--manifest", "x.json"], env=_base_env())


def test_manifest_with_base_urls_multi_site_raises_config_error():
    # TestID: CFG-005
    # Multi-site mode is entered via BASE_URLS when no CLI url is given;
    # if --manifest is also supplied it should raise ConfigError.
    with pytest.raises(ConfigError):
        load_config(["--manifest", "x.json"], env=_base_env(BASE_URLS="https://a.com"))


def test_max_pages_missing_raises_config_error():
    # TestID: CFG-006
    with pytest.raises(ConfigError):
        load_config(["https://a.com"], env={"TIMEOUT_SECONDS": "30"})


def test_timeout_seconds_missing_raises_config_error():
    # TestID: CFG-007
    with pytest.raises(ConfigError):
        load_config(["https://a.com"], env={"MAX_PAGES": "1000"})


def test_invalid_mode_raises_config_error():
    # TestID: CFG-008
    with pytest.raises(ConfigError):
        load_config(["https://a.com"], env=_base_env(MODE="invalid"))


def test_invalid_url_scheme_raises_config_error():
    # TestID: CFG-009
    with pytest.raises(ConfigError):
        load_config(["ftp://a.com"], env=_base_env())


def test_max_pages_non_numeric_raises_config_error():
    # TestID: CFG-010
    with pytest.raises(ConfigError):
        load_config(["https://a.com"], env=_base_env(MAX_PAGES="abc"))


def test_cli_log_level_overrides_env_log_level():
    # TestID: CFG-011
    config = load_config(
        ["https://a.com", "--log-level", "DEBUG"], env=_base_env(LOG_LEVEL="ERROR"),
    )
    assert config.log_level == "DEBUG"


def test_default_values_applied_when_optional_env_missing():
    # TestID: CFG-012
    config = load_config(["https://a.com"], env=_base_env())
    assert config.word_limit == 450000
    assert config.request_delay == 0.5


def test_include_exclude_csv_parsed_correctly():
    # TestID: CFG-013
    config = load_config(["https://a.com"], env=_base_env(INCLUDE="/a, /b"))
    assert config.include == ["/a", "/b"]


def test_invalid_log_level_raises_config_error():
    # TestID: CFG-014
    with pytest.raises(ConfigError):
        load_config(["https://a.com"], env=_base_env(LOG_LEVEL="TRACE"))


def test_invalid_log_format_raises_config_error():
    # TestID: CFG-015
    with pytest.raises(ConfigError):
        load_config(["https://a.com"], env=_base_env(LOG_FORMAT="xml"))


def test_cli_url_takes_priority_over_base_urls():
    # TestID: CFG-016
    config = load_config(
        ["https://a.com"], env=_base_env(BASE_URLS="https://b.com"),
    )
    assert config.url == "https://a.com"
    assert config.base_urls == []


def test_word_limit_or_request_delay_non_numeric_raises_config_error():
    # TestID: CFG-017
    with pytest.raises(ConfigError):
        load_config(["https://a.com"], env=_base_env(WORD_LIMIT="abc"))

    with pytest.raises(ConfigError):
        load_config(["https://a.com"], env=_base_env(REQUEST_DELAY="xyz"))
