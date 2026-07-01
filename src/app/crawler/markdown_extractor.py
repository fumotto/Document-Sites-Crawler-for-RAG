"""MarkdownExtractor（04_モジュール設計.md / 要件定義書12, 13節）。

trafilatura を用いて本文抽出を行い、Markdown形式（コードブロック保持）で
返却する。title・language の抽出も担当する。

注意: trafilatura は requirements.txt に記載の依存ライブラリであり、
実行環境（Docker image）に必ずインストールされる前提とする。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    import trafilatura
    from trafilatura.settings import use_config

    _TRAFILATURA_AVAILABLE = True
except ImportError:  # 開発環境等でtrafilatura未インストールの場合のフォールバック
    trafilatura = None  # type: ignore
    _TRAFILATURA_AVAILABLE = False


@dataclass
class ExtractionResult:
    title: Optional[str]
    language: Optional[str]
    body_markdown: Optional[str]


class MarkdownExtractor:
    """trafilaturaベースの本文抽出。コードブロックを保持するMarkdown形式で出力する。"""

    def extract(self, html: str, url: str) -> ExtractionResult:
        if not _TRAFILATURA_AVAILABLE:
            # trafilatura未インストール環境向けの最小フォールバック（開発・テスト用途）。
            # 本番実行時は requirements.txt により trafilatura が必ずインストールされる。
            return self._fallback_extract(html, url)

        config = use_config()
        config.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")

        body_markdown = trafilatura.extract(
            html,
            url=url,
            output_format="markdown",
            include_tables=True,
            include_formatting=True,
            include_links=False,
            favor_precision=False,
            config=config,
        )

        metadata = trafilatura.extract_metadata(html, default_url=url)
        title = metadata.title if metadata else None
        language = metadata.language if metadata else None

        return ExtractionResult(title=title, language=language, body_markdown=body_markdown)

    @staticmethod
    def _fallback_extract(html: str, url: str) -> ExtractionResult:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else None
        body_tag = soup.find("body")
        text = body_tag.get_text("\n", strip=True) if body_tag else soup.get_text("\n", strip=True)
        return ExtractionResult(title=title, language=None, body_markdown=text or None)
