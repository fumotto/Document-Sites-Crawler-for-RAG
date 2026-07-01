"""ManifestRepository（04_モジュール設計.md 4節 / 05_データ構造設計.md）。

manifest.json の読み書きを担当する。マージ更新ルール（05節）に従い、
crawl_result の種別に応じて更新するフィールドを制御する。
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

from src.app.mapper.manifest_mapper import document_to_manifest_dict, manifest_dict_to_document
from src.app.models.crawl_result import CrawlResult
from src.app.models.manifest_record import ManifestRecord
from src.app.utils.atomic_io import atomic_write_json, read_json

# NOT_MODIFIED はmanifestへの書き込みを行わない（05節）
_FULL_UPDATE_RESULTS = {CrawlResult.SUCCESS}
_PARTIAL_UPDATE_RESULTS = {
    CrawlResult.NETWORK_ERROR,
    CrawlResult.TIMEOUT,
    CrawlResult.SERVER_ERROR,
    CrawlResult.TOO_MANY_REQUESTS,
    CrawlResult.NOT_FOUND,
    CrawlResult.ROBOTS_DENIED,
}


class ManifestRepository:
    def __init__(self, manifest_path: Path):
        self._manifest_path = manifest_path

    def load(self) -> Dict[str, ManifestRecord]:
        """{normalized_url: ManifestRecord} を返す。ファイル未存在時は空辞書。"""
        if not self._manifest_path.exists():
            return {}
        document = read_json(self._manifest_path)
        return document_to_manifest_dict(document)

    def save(self, pages: Dict[str, ManifestRecord]) -> None:
        document = manifest_dict_to_document(pages)
        atomic_write_json(self._manifest_path, document)

    def merge_update(self, url: str, new_record: ManifestRecord) -> None:
        """1件をマージ更新する（05節 マージ更新ルール）。

        - SUCCESS: 全フィールドを更新
        - NETWORK_ERROR/TIMEOUT/SERVER_ERROR/TOO_MANY_REQUESTS/NOT_FOUND/ROBOTS_DENIED:
          last_crawled, crawl_result のみ更新。他は既存値を保持する。
        - NOT_MODIFIED: 書き込みを行わない（呼び出し側で除外される想定だが、念のためガードする）
        """
        if new_record.crawl_result == CrawlResult.NOT_MODIFIED:
            return

        pages = self.load()
        existing = pages.get(url)

        if new_record.crawl_result in _FULL_UPDATE_RESULTS or existing is None:
            pages[url] = new_record
        elif new_record.crawl_result in _PARTIAL_UPDATE_RESULTS:
            pages[url] = ManifestRecord(
                page_hash=existing.page_hash,
                etag=existing.etag,
                last_modified=existing.last_modified,
                sitemap_lastmod=existing.sitemap_lastmod,
                content_sha256=existing.content_sha256,
                last_crawled=new_record.last_crawled,
                crawl_result=new_record.crawl_result,
            )
        else:
            pages[url] = new_record

        self.save(pages)

    def delete(self, url: str) -> None:
        pages = self.load()
        if url in pages:
            del pages[url]
            self.save(pages)

    def delete_many(self, urls: set) -> None:
        if not urls:
            return
        pages = self.load()
        changed = False
        for url in urls:
            if url in pages:
                del pages[url]
                changed = True
        if changed:
            self.save(pages)
