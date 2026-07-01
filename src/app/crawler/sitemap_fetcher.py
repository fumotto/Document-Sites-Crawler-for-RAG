"""SitemapFetcher（04_モジュール設計.md / 要件定義書6節）。

sitemap.xml（および sitemap index の再帰展開）を取得し、(url, lastmod) の
リストを返す。

再帰段数の上限ガード:
    「02_基本設計書」9節「今後の課題」で指摘されていた sitemap index の
    再帰展開の上限未規定について、本実装では MAX_SITEMAP_DEPTH で上限を
    設ける（異常なsitemapによる無限再帰・過大なリクエストを防止するため）。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin

import requests
from lxml import etree

MAX_SITEMAP_DEPTH = 5
_SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


@dataclass
class SitemapEntry:
    url: str
    lastmod: Optional[str]


class SitemapFetcher:
    def __init__(self, user_agent: str, timeout_seconds: int, session: requests.Session | None = None):
        self._user_agent = user_agent
        self._timeout_seconds = timeout_seconds
        self._session = session or requests.Session()

    def fetch(self, base_url: str, extra_sitemap_urls: Optional[List[str]] = None) -> List[SitemapEntry]:
        """sitemap.xml（既定パス）＋ robots.txt記載分を統合して取得する。

        いずれのsitemapも取得できない場合は空リストを返す
        （呼び出し側 CrawlerService がフォールバッククロールへ移行する）。
        """
        candidates: List[str] = []
        if extra_sitemap_urls:
            candidates.extend(extra_sitemap_urls)
        candidates.append(urljoin(base_url, "/sitemap.xml"))

        seen_urls: set = set()
        entries: List[SitemapEntry] = []
        for candidate in candidates:
            entries.extend(self._fetch_recursive(candidate, depth=0, seen=seen_urls))
        # 重複除去（URL単位）
        deduped = {}
        for e in entries:
            deduped[e.url] = e  # 後勝ち（lastmodが新しい情報で上書きされる想定）
        return list(deduped.values())

    def _fetch_recursive(self, sitemap_url: str, depth: int, seen: set) -> List[SitemapEntry]:
        if sitemap_url in seen:
            return []
        seen.add(sitemap_url)

        if depth > MAX_SITEMAP_DEPTH:
            return []

        try:
            response = self._session.get(
                sitemap_url, timeout=self._timeout_seconds,
                headers={"User-Agent": self._user_agent},
            )
            if response.status_code != 200:
                return []
            root = etree.fromstring(response.content)
        except Exception:
            return []

        tag = etree.QName(root.tag).localname

        if tag == "sitemapindex":
            results: List[SitemapEntry] = []
            for sitemap_el in root.findall("sm:sitemap", _SITEMAP_NS):
                loc_el = sitemap_el.find("sm:loc", _SITEMAP_NS)
                if loc_el is None or not loc_el.text:
                    continue
                results.extend(self._fetch_recursive(loc_el.text.strip(), depth + 1, seen))
            return results

        if tag == "urlset":
            results = []
            for url_el in root.findall("sm:url", _SITEMAP_NS):
                loc_el = url_el.find("sm:loc", _SITEMAP_NS)
                if loc_el is None or not loc_el.text:
                    continue
                lastmod_el = url_el.find("sm:lastmod", _SITEMAP_NS)
                lastmod = lastmod_el.text.strip() if lastmod_el is not None and lastmod_el.text else None
                results.append(SitemapEntry(url=loc_el.text.strip(), lastmod=lastmod))
            return results

        return []
