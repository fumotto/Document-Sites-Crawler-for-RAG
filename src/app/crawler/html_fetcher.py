"""HtmlFetcher（04_モジュール設計.md / 要件定義書9, 25, 26, 27節）。

HTML取得を担当する。条件付きリクエスト（If-None-Match / If-Modified-Since）、
リダイレクト追跡（最大5ホップ、06_処理シーケンス.md 4節）、タイムアウト、
エラー種別ごとの例外送出を行う。
"""
from __future__ import annotations

from typing import Optional

import requests

from src.app.crawler.types import HttpResponse
from src.app.exceptions.errors import (
    CrawlTimeoutError,
    NetworkError,
    NotFoundError,
    ServerError,
    TooManyRequestsError,
)

MAX_REDIRECT_HOPS = 5


class HtmlFetcher:
    def __init__(self, user_agent: str, timeout_seconds: int, session: requests.Session | None = None):
        self._user_agent = user_agent
        self._timeout_seconds = timeout_seconds
        self._session = session or requests.Session()

    def fetch(
        self,
        url: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
    ) -> HttpResponse:
        """URLを取得する。

        Raises:
            NotFoundError: 404
            ServerError: 5xx
            TooManyRequestsError: 429
            NetworkError: 接続エラー・DNSエラー等
            CrawlTimeoutError: タイムアウト
        """
        headers = {"User-Agent": self._user_agent}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        try:
            response = self._session.get(
                url,
                headers=headers,
                timeout=self._timeout_seconds,
                allow_redirects=False,
            )
        except requests.exceptions.Timeout as exc:
            raise CrawlTimeoutError(f"Timeout while fetching {url}") from exc
        except requests.exceptions.RequestException as exc:
            raise NetworkError(f"Network error while fetching {url}: {exc}") from exc

        hops = 0
        current_url = url
        while response.status_code in (301, 302, 303, 307, 308):
            hops += 1
            if hops > MAX_REDIRECT_HOPS:
                raise NetworkError(f"Exceeded max redirect hops ({MAX_REDIRECT_HOPS}) for {url}")
            location = response.headers.get("Location")
            if not location:
                break
            current_url = requests.compat.urljoin(current_url, location)
            try:
                response = self._session.get(
                    current_url, headers=headers, timeout=self._timeout_seconds,
                    allow_redirects=False,
                )
            except requests.exceptions.Timeout as exc:
                raise CrawlTimeoutError(f"Timeout while fetching {current_url}") from exc
            except requests.exceptions.RequestException as exc:
                raise NetworkError(f"Network error while fetching {current_url}: {exc}") from exc

        status = response.status_code

        if status == 304:
            return HttpResponse(
                status_code=304, url=current_url, text=None,
                etag=response.headers.get("ETag"),
                last_modified=response.headers.get("Last-Modified"),
                content_type=None,
            )
        if status == 404:
            raise NotFoundError(f"404 Not Found: {url}")
        if status == 429:
            retry_after = response.headers.get("Retry-After")
            raise TooManyRequestsError(
                f"429 Too Many Requests: {url} (Retry-After={retry_after})"
            )
        if 500 <= status < 600:
            raise ServerError(f"{status} Server Error: {url}")
        if not (200 <= status < 300):
            raise NetworkError(f"Unexpected status {status} for {url}")

        return HttpResponse(
            status_code=status,
            url=current_url,
            text=response.text,
            etag=response.headers.get("ETag"),
            last_modified=response.headers.get("Last-Modified"),
            content_type=response.headers.get("Content-Type"),
        )
