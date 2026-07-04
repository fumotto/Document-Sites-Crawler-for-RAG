from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.app.crawler.html_fetcher import HtmlFetcher
from src.app.exceptions.errors import (
    CrawlTimeoutError,
    NetworkError,
    NotFoundError,
    ServerError,
    TooManyRequestsError,
)


def _resp(status_code, text=None, headers=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.headers = headers or {}
    return resp


def test_200_ok_returns_populated_response():
    # TestID: HF-001
    def fake_get(self, url, headers=None, timeout=None, follow_redirects=None):
        return _resp(200, text="<html>hi</html>", headers={"ETag": '"abc"', "Last-Modified": "Tue"})

    with patch.object(httpx.Client, "get", fake_get):
        fetcher = HtmlFetcher("agent", 10)
        result = fetcher.fetch("https://example.com/a")

    assert result.status_code == 200
    assert result.text == "<html>hi</html>"
    assert result.etag == '"abc"'
    assert result.last_modified == "Tue"


def test_304_not_modified_returns_no_text():
    # TestID: HF-002
    def fake_get(self, url, headers=None, timeout=None, follow_redirects=None):
        return _resp(304, text=None, headers={"ETag": '"abc"'})

    with patch.object(httpx.Client, "get", fake_get):
        fetcher = HtmlFetcher("agent", 10)
        result = fetcher.fetch("https://example.com/a")

    assert result.status_code == 304
    assert result.text is None


def test_404_raises_not_found_error():
    # TestID: HF-003
    def fake_get(self, url, headers=None, timeout=None, follow_redirects=None):
        return _resp(404)

    with patch.object(httpx.Client, "get", fake_get):
        fetcher = HtmlFetcher("agent", 10)
        with pytest.raises(NotFoundError):
            fetcher.fetch("https://example.com/missing")


def test_429_raises_too_many_requests_error():
    # TestID: HF-004
    def fake_get(self, url, headers=None, timeout=None, follow_redirects=None):
        return _resp(429, headers={"Retry-After": "30"})

    with patch.object(httpx.Client, "get", fake_get):
        fetcher = HtmlFetcher("agent", 10)
        with pytest.raises(TooManyRequestsError):
            fetcher.fetch("https://example.com/a")


def test_5xx_raises_server_error():
    # TestID: HF-005
    def fake_get(self, url, headers=None, timeout=None, follow_redirects=None):
        return _resp(500)

    with patch.object(httpx.Client, "get", fake_get):
        fetcher = HtmlFetcher("agent", 10)
        with pytest.raises(ServerError):
            fetcher.fetch("https://example.com/a")


def test_timeout_raises_crawl_timeout_error():
    # TestID: HF-006
    def fake_get(self, url, headers=None, timeout=None, follow_redirects=None):
        raise httpx.TimeoutException("timed out")

    with patch.object(httpx.Client, "get", fake_get):
        fetcher = HtmlFetcher("agent", 10)
        with pytest.raises(CrawlTimeoutError):
            fetcher.fetch("https://example.com/a")


def test_connection_error_raises_network_error():
    # TestID: HF-007
    def fake_get(self, url, headers=None, timeout=None, follow_redirects=None):
        raise httpx.ConnectError("connection refused")

    with patch.object(httpx.Client, "get", fake_get):
        fetcher = HtmlFetcher("agent", 10)
        with pytest.raises(NetworkError):
            fetcher.fetch("https://example.com/a")


def test_redirect_followed_within_hop_limit():
    # TestID: HF-008
    call_count = {"n": 0}

    def fake_get(self, url, headers=None, timeout=None, follow_redirects=None):
        call_count["n"] += 1
        if call_count["n"] <= 3:
            return _resp(302, headers={"Location": f"/next{call_count['n']}"})
        return _resp(200, text="final content")

    with patch.object(httpx.Client, "get", fake_get):
        fetcher = HtmlFetcher("agent", 10)
        result = fetcher.fetch("https://example.com/start")

    assert result.status_code == 200
    assert result.text == "final content"


def test_exceeding_max_redirect_hops_raises_network_error():
    # TestID: HF-009
    def fake_get(self, url, headers=None, timeout=None, follow_redirects=None):
        return _resp(302, headers={"Location": "/next"})

    with patch.object(httpx.Client, "get", fake_get):
        fetcher = HtmlFetcher("agent", 10)
        with pytest.raises(NetworkError):
            fetcher.fetch("https://example.com/start")


def test_etag_and_last_modified_sent_as_conditional_headers():
    # TestID: HF-010
    captured_headers = {}

    def fake_get(self, url, headers=None, timeout=None, follow_redirects=None):
        captured_headers.update(headers or {})
        return _resp(200, text="body")

    with patch.object(httpx.Client, "get", fake_get):
        fetcher = HtmlFetcher("agent", 10)
        fetcher.fetch("https://example.com/a", etag='"abc"', last_modified="Tue, 01 Jan 2026")

    assert captured_headers.get("If-None-Match") == '"abc"'
    assert captured_headers.get("If-Modified-Since") == "Tue, 01 Jan 2026"


def test_unexpected_status_code_raises_network_error():
    # TestID: HF-011
    def fake_get(self, url, headers=None, timeout=None, follow_redirects=None):
        return _resp(418)  # I'm a teapot - unexpected non-2xx, non-redirect status

    with patch.object(httpx.Client, "get", fake_get):
        fetcher = HtmlFetcher("agent", 10)
        with pytest.raises(NetworkError):
            fetcher.fetch("https://example.com/a")


def test_redirect_without_location_header_breaks_loop_and_returns_response():
    # TestID: HF-012
    def fake_get(self, url, headers=None, timeout=None, follow_redirects=None):
        return _resp(302, headers={})  # no Location header

    with patch.object(httpx.Client, "get", fake_get):
        fetcher = HtmlFetcher("agent", 10)
        with pytest.raises(NetworkError):
            # After breaking the redirect loop, status=302 falls through to
            # the "not (200 <= status < 300)" branch, raising NetworkError.
            fetcher.fetch("https://example.com/a")


def test_timeout_during_redirect_follow_raises_crawl_timeout_error():
    # TestID: HF-013
    call_count = {"n": 0}

    def fake_get(self, url, headers=None, timeout=None, follow_redirects=None):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _resp(302, headers={"Location": "/next"})
        raise httpx.TimeoutException("timed out on redirect target")

    with patch.object(httpx.Client, "get", fake_get):
        fetcher = HtmlFetcher("agent", 10)
        with pytest.raises(CrawlTimeoutError):
            fetcher.fetch("https://example.com/start")
