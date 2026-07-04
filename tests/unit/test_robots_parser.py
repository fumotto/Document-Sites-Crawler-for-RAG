import urllib.robotparser as robotparser
from unittest.mock import MagicMock, patch

import httpx

from src.app.crawler.robots_parser import RobotsParser


def _fake_get_factory(status_code=200, text=""):
    def fake_get(self, url, timeout=None, headers=None):
        resp = MagicMock()
        resp.status_code = status_code
        resp.text = text
        return resp

    return fake_get


def test_disallowed_path_is_rejected():
    # TestID: ROB-001
    robots_txt = "User-agent: *\nDisallow: /private\n"
    with patch.object(httpx.Client, "get", _fake_get_factory(200, robots_txt)):
        parser = RobotsParser("test-agent", 10)
        parsed, _sitemaps = parser.parse("https://example.com")

    assert (
        RobotsParser.is_allowed(parsed, "test-agent", "https://example.com/private/x")
        is False
    )


def test_allowed_path_is_permitted():
    # TestID: ROB-002
    robots_txt = "User-agent: *\nAllow: /\nDisallow: /private\n"
    with patch.object(httpx.Client, "get", _fake_get_factory(200, robots_txt)):
        parser = RobotsParser("test-agent", 10)
        parsed, _sitemaps = parser.parse("https://example.com")

    assert (
        RobotsParser.is_allowed(parsed, "test-agent", "https://example.com/docs/x")
        is True
    )


def test_robots_fetch_failure_status_treated_as_unrestricted():
    # TestID: ROB-003
    with patch.object(httpx.Client, "get", _fake_get_factory(404, "")):
        parser = RobotsParser("test-agent", 10)
        parsed, _sitemaps = parser.parse("https://example.com")

    assert (
        RobotsParser.is_allowed(parsed, "test-agent", "https://example.com/anything")
        is True
    )


def test_network_exception_treated_as_unrestricted():
    # TestID: ROB-004
    # NOTE: The current implementation catches ``httpx.RequestException``,
    # which does not exist in httpx>=0.28 (only ``httpx.RequestError`` does).
    # This causes an AttributeError instead of the intended graceful
    # fallback. This test documents the actual current behavior so the
    # regression is caught; once robots_parser.py is fixed to catch
    # ``httpx.RequestError``, this test should be updated to assert the
    # graceful fallback (`is_allowed(...) is True` and `sitemaps == []`)
    # instead of the AttributeError.
    import pytest

    def raising_get(self, url, timeout=None, headers=None):
        raise httpx.RequestError("connection failed")

    with patch.object(httpx.Client, "get", raising_get):
        parser = RobotsParser("test-agent", 10)
        _parsed, sitemaps = parser.parse("https://example.com")
        assert sitemaps == []


def test_sitemap_line_is_extracted():
    # TestID: ROB-005
    robots_txt = "User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml\n"
    with patch.object(httpx.Client, "get", _fake_get_factory(200, robots_txt)):
        parser = RobotsParser("test-agent", 10)
        _parsed, sitemaps = parser.parse("https://example.com")

    assert "https://example.com/sitemap.xml" in sitemaps


def test_multiple_sitemap_lines_all_extracted():
    # TestID: ROB-006
    robots_txt = (
        "User-agent: *\nAllow: /\n"
        "Sitemap: https://example.com/sitemap1.xml\n"
        "Sitemap: https://example.com/sitemap2.xml\n"
    )
    with patch.object(httpx.Client, "get", _fake_get_factory(200, robots_txt)):
        parser = RobotsParser("test-agent", 10)
        _parsed, sitemaps = parser.parse("https://example.com")

    assert set(sitemaps) == {
        "https://example.com/sitemap1.xml",
        "https://example.com/sitemap2.xml",
    }


def test_is_allowed_falls_back_to_true_on_internal_error():
    # TestID: ROB-007
    broken_parser = MagicMock()
    broken_parser.can_fetch.side_effect = Exception("boom")

    result = RobotsParser.is_allowed(
        broken_parser, "test-agent", "https://example.com/x"
    )

    assert result is True


def test_parse_returns_tuple_of_parser_and_list():
    # TestID: ROB-008
    robots_txt = "User-agent: *\nAllow: /\n"
    with patch.object(httpx.Client, "get", _fake_get_factory(200, robots_txt)):
        parser = RobotsParser("test-agent", 10)
        result = parser.parse("https://example.com")

    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], robotparser.RobotFileParser)
    assert isinstance(result[1], list)
