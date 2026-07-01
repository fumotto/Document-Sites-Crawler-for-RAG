"""ChunkBuilder（要件定義書16, 17節）。

WORD_LIMITに基づき結合Markdown（docs_XXX.md）を生成する。
1ページが複数ファイルに跨ることはない。単体で WORD_LIMIT を超えるページは
単独ファイル化し、警告ログを出す。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Tuple

from src.app.models.chunk_record import ChunkRecord
from src.app.models.page_metadata_record import PageMetadataRecord

logger = logging.getLogger(__name__)


@dataclass
class ChunkFile:
    filename: str
    content: str


@dataclass
class ChunkBuildResult:
    files: List[ChunkFile]
    chunk_records: List[ChunkRecord]
    warnings: List[str]


class ChunkBuilder:
    def build_chunks(
        self,
        ordered_pages: List[Tuple[str, PageMetadataRecord]],
        page_bodies: dict,  # {page_hash: body_markdown}
        word_limit: int,
    ) -> ChunkBuildResult:
        files: List[ChunkFile] = []
        chunk_records: List[ChunkRecord] = []
        warnings: List[str] = []

        current_parts: List[str] = []
        current_word_count = 0
        current_index = 1
        # ページとファイルの対応（save後にfilenameを割り当てるための一時保持）
        pending_records: List[Tuple[str, PageMetadataRecord]] = []

        def flush():
            nonlocal current_parts, current_word_count, current_index, pending_records
            if not current_parts:
                return
            filename = f"docs_{current_index:03d}.md"
            files.append(ChunkFile(filename=filename, content="\n\n---\n\n".join(current_parts)))
            for page_hash, record in pending_records:
                chunk_records.append(
                    ChunkRecord(
                        title=record.title or record.url,
                        url=record.url,
                        file=filename,
                        sha256=record.content_sha256,
                        word_count=record.word_count,
                    )
                )
            current_parts = []
            current_word_count = 0
            current_index += 1
            pending_records = []

        for page_hash, record in ordered_pages:
            body = page_bodies.get(page_hash, "")
            page_word_count = record.word_count

            if page_word_count > word_limit:
                # 単体でWORD_LIMITを超過するページは単独ファイル化する
                flush()  # 現在バッファ中の内容を先に確定する
                filename = f"docs_{current_index:03d}.md"
                files.append(ChunkFile(filename=filename, content=body))
                chunk_records.append(
                    ChunkRecord(
                        title=record.title or record.url, url=record.url, file=filename,
                        sha256=record.content_sha256, word_count=record.word_count,
                    )
                )
                current_index += 1
                warnings.append(
                    f"Page exceeds WORD_LIMIT and was written to its own file: "
                    f"{record.url} ({page_word_count} words > {word_limit})"
                )
                logger.warning(
                    "Page exceeds WORD_LIMIT, written to own file: %s (%s > %s)",
                    record.url, page_word_count, word_limit,
                )
                continue

            if current_word_count + page_word_count > word_limit and current_parts:
                flush()

            current_parts.append(body)
            current_word_count += page_word_count
            pending_records.append((page_hash, record))

        flush()

        return ChunkBuildResult(files=files, chunk_records=chunk_records, warnings=warnings)
