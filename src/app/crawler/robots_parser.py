"""RobotsParser（04_モジュール設計.md / 要件定義書9節）。

robots.txt を取得・解析し、User-Agent に対するアクセス許可判定と、
robots.txt に記載された Sitemap URL 一覧を提供する。
"""
from __future__ import annotations

import urllib.robotparser as robotparser
from typing import List
from urllib.parse import urljoin, urlsplit

import requests

from src.app.crawler.types import RobotsInfo


class RobotsParser:
    def __init__(self, user_agent: str, timeout_seconds: int, session: requests.Session | None = None):
        self._user_agent = user_agent
        self._timeout_seconds = timeout_seconds
        self._session = session or requests.Session()

    def parse(self, base_url: str) -> tuple:
        """robots.txt を取得し、(RobotParser, List[sitemap_url]) を返す。

        取得に失敗した場合はアクセス制限なしとみなし、空のRobotParserを返す
        （要件定義書9節: robots.txtが存在しない場合は制限なしとして扱う）。
        """
        parts = urlsplit(base_url)
        robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"

        parser = robotparser.RobotFileParser()
        sitemap_urls: List[str] = []

        try:
            response = self._session.get(
                robots_url, timeout=self._timeout_seconds,
                headers={"User-Agent": self._user_agent},
            )
            if response.status_code == 200:
                lines = response.text.splitlines()
                parser.parse(lines)
                for line in lines:
                    if line.strip().lower().startswith("sitemap:"):
                        sitemap_url = line.split(":", 1)[1].strip()
                        sitemap_urls.append(urljoin(base_url, sitemap_url))
            else:
                parser.parse([])
        except requests.RequestException:
            parser.parse([])

        return parser, sitemap_urls

    @staticmethod
    def is_allowed(parser: robotparser.RobotFileParser, user_agent: str, url: str) -> bool:
        try:
            return parser.can_fetch(user_agent, url)
        except Exception:
            return True
