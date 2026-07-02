"""StatisticsCalculator（04_モジュール設計.md / 要件定義書30節）。

word_count / char_count / token_count（tiktokenによる推定値）を算出する。

注意: token_count はtiktoken（cl100k_base）による推定値であり、
NotebookLM（Gemini系）の実トークン数とは一致しない目安値である
（要件定義書30節 / 02_基本設計書 6節）。

RISK-1対応（08_デスクトップアプリ化要件定義書.md）:
    tiktokenの `get_encoding("cl100k_base")` はエンコーディングデータを
    初回利用時にネットワーク経由で取得する実装になっており、オフライン環境や
    社内ネットワーク制限下では失敗しうる。Docker版と異なりデスクトップアプリ版は
    オフライン環境で利用される可能性が上がるため、ImportError以外の例外
    （ネットワークエラー等）も広く捕捉し、確実に文字数ベースの推定へ
    フォールバックする。
"""
from __future__ import annotations

import logging

from src.app.models.stats_record import StatsRecord

logger = logging.getLogger(__name__)

_ENCODING = None
_TIKTOKEN_AVAILABLE = False

try:
    import tiktoken

    try:
        _ENCODING = tiktoken.get_encoding("cl100k_base")
        _TIKTOKEN_AVAILABLE = True
    except Exception:  # ネットワークエラー・オフライン環境等、ImportError以外の失敗も含む
        logger.warning(
            "Failed to initialize tiktoken encoding (offline environment?). "
            "Falling back to character-based token estimation.",
            exc_info=True,
        )
        _ENCODING = None
        _TIKTOKEN_AVAILABLE = False
except ImportError:  # 開発環境等でtiktoken未インストールの場合のフォールバック
    _ENCODING = None
    _TIKTOKEN_AVAILABLE = False


class StatisticsCalculator:
    def calculate(self, body_markdown: str) -> StatsRecord:
        char_count = len(body_markdown)
        word_count = len(body_markdown.split())
        token_count = self._estimate_token_count(body_markdown, char_count)
        return StatsRecord(word_count=word_count, char_count=char_count, token_count=token_count)

    @staticmethod
    def _estimate_token_count(body_markdown: str, char_count: int) -> int:
        global _TIKTOKEN_AVAILABLE

        if _TIKTOKEN_AVAILABLE and _ENCODING is not None:
            try:
                return len(_ENCODING.encode(body_markdown))
            except Exception:
                # 実行時に何らかの理由でエンコードに失敗した場合も、処理全体を
                # 止めずに文字数ベースの推定へフォールバックする。
                logger.warning("tiktoken encode() failed; falling back to estimation.", exc_info=True)
                _TIKTOKEN_AVAILABLE = False

        # tiktoken未インストール／初期化失敗環境向けの粗い推定（英語目安: 4文字/token）。
        return max(1, char_count // 4)
