"""DuplicateResolver（要件定義書18節 / 05_データ構造設計.md / 06_処理シーケンス.md 5節）。

Builderがビルドのたびに全metadataを照合して重複判定を行う。manifestには
重複フラグを保持しない。

判定ロジック:
    1. content_sha256でグループ化する
    2. 同一content_sha256を持つページが複数存在する場合、retrieved_atが
       最も新しいページを正として残す（後から見つかったURL優先）
    3. それ以外のページは結合Markdown・chunk_manifest.json・Index.mdへの
       出力対象から除外する
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from src.app.models.page_metadata_record import PageMetadataRecord


@dataclass
class DuplicateResolution:
    canonical: List[Tuple[str, PageMetadataRecord]]   # [(page_hash, record), ...] 採用ページ
    excluded: List[Tuple[str, PageMetadataRecord]]     # 重複により除外されたページ


class DuplicateResolver:
    def resolve(self, metadata_list: List[Tuple[str, PageMetadataRecord]]) -> DuplicateResolution:
        groups: Dict[str, List[Tuple[str, PageMetadataRecord]]] = {}
        for page_hash, record in metadata_list:
            groups.setdefault(record.content_sha256, []).append((page_hash, record))

        canonical: List[Tuple[str, PageMetadataRecord]] = []
        excluded: List[Tuple[str, PageMetadataRecord]] = []

        for _sha256, items in groups.items():
            if len(items) == 1:
                canonical.append(items[0])
                continue
            # retrieved_atが最も新しいものを正とする
            sorted_items = sorted(items, key=lambda item: item[1].retrieved_at, reverse=True)
            canonical.append(sorted_items[0])
            excluded.extend(sorted_items[1:])

        return DuplicateResolution(canonical=canonical, excluded=excluded)
