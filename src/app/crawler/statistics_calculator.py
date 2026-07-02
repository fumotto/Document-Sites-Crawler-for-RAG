"""StatisticsCalculator（04_モジュール設計.md / 要件定義書30節）。

word_count / char_count / token_count（tiktokenによる推定値）を算出する。

注意: token_count はtiktoken（cl100k_base）による推定値であり、
NotebookLM（Gemini系）の実トークン数とは一致しない目安値である
（要件定義書30節 / 02_基本設計書 6節）。
"""
from __future__ import annotations

from src.app.models.stats_record import StatsRecord

try:
    import tiktoken

    _ENCODING = tiktoken.get_encoding("cl100k_base")
    _TIKTOKEN_AVAILABLE = True
except ImportError:  # 開発環境等でtiktoken未インストールの場合のフォールバック
    _ENCODING = None
    _TIKTOKEN_AVAILABLE = False


class StatisticsCalculator:
    def calculate(self, body_markdown: str) -> StatsRecord:
        char_count = len(body_markdown)
        word_count = len(body_markdown.split())

        if _TIKTOKEN_AVAILABLE:
            token_count = len(_ENCODING.encode(body_markdown))
        else:
            # tiktoken未インストール環境向けの粗い推定（英語目安: 4文字/token）。
            # 本番実行時は requirements.txt により tiktoken が必ずインストールされる。
            token_count = max(1, char_count // 4)

        return StatsRecord(word_count=word_count, char_count=char_count, token_count=token_count)
