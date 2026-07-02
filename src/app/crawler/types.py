"""クローラー内部限定の型（永続化されない。Mapperを経由しない）。

06_処理シーケンス.md のシーケンス図に登場する RobotsInfo / HttpResponse に
対応する。DTO層（models/）とは異なり、CrawlerService 内部でのみ使用する。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class HttpResponse:
    status_code: int
    url: str                       # リダイレクト後の最終URL
    text: Optional[str]
    etag: Optional[str]
    last_modified: Optional[str]
    content_type: Optional[str]
    retry_after: Optional[float] = None


@dataclass
class RobotsInfo:
    allowed_paths_checked: bool
    sitemap_urls: list

    def is_allowed(self, path: str) -> bool:  # pragma: no cover - 委譲用の簡易実装
        return True
