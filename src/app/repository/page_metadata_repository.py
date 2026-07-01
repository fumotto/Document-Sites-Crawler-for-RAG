"""PageMetadataRepository（04_モジュール設計.md 4節 / 05_データ構造設計.md）。

metadata/{page_hash}.json の読み書きを担当する。crawl_result=SUCCESS の
ページのみが書き込み対象となる（呼び出し側であるCrawlerServiceが制御する）。
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from src.app.mapper.page_metadata_mapper import dict_to_page_metadata, page_metadata_to_dict
from src.app.models.page_metadata_record import PageMetadataRecord
from src.app.utils.atomic_io import atomic_write_json, read_json


class PageMetadataRepository:
    def __init__(self, metadata_dir: Path):
        self._metadata_dir = metadata_dir

    def _path_for(self, page_hash: str) -> Path:
        return self._metadata_dir / f"{page_hash}.json"

    def save(self, page_hash: str, record: PageMetadataRecord) -> None:
        atomic_write_json(self._path_for(page_hash), page_metadata_to_dict(record))

    def load(self, page_hash: str) -> PageMetadataRecord:
        return dict_to_page_metadata(read_json(self._path_for(page_hash)))

    def exists(self, page_hash: str) -> bool:
        return self._path_for(page_hash).exists()

    def delete(self, page_hash: str) -> None:
        path = self._path_for(page_hash)
        if path.exists():
            path.unlink()

    def load_all(self) -> List[tuple]:
        """全metadataを読み込む。[(page_hash, PageMetadataRecord), ...] を返す（ビルド用途）。"""
        results = []
        if not self._metadata_dir.exists():
            return results
        for path in sorted(self._metadata_dir.glob("*.json")):
            page_hash = path.stem
            results.append((page_hash, dict_to_page_metadata(read_json(path))))
        return results
