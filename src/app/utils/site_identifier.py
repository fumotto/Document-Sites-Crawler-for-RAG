"""
サイト識別子生成ユーティリティ。

「03_ディレクトリ構成.md」の命名ルールに従い、URLからサイト識別子を機械的に生成する。

手順:
    1. スキーム（https:// 等）を除去する
    2. ホスト名およびパスを含め、すべて小文字化する
    3. 英数字以外の文字（/ . : - 等）は _ に置換する
    4. _ が連続する場合は1文字へ圧縮する
    5. 先頭・末尾の _ は除去する

末尾スラッシュの有無のみが異なるURLは同一サイト識別子となる。これは仕様であり、
識別子の衝突としては扱わない（03_ディレクトリ構成.md 参照）。
"""
from __future__ import annotations

import re

_SCHEME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://")
_NON_ALNUM_PATTERN = re.compile(r"[^a-z0-9]+")


def generate_site_identifier(url: str) -> str:
    """URLからサイト識別子を生成する。

    Args:
        url: 対象URL（例: "https://supabase.com/docs/"）

    Returns:
        サイト識別子（例: "supabase_com_docs"）

    Raises:
        ValueError: 生成結果が空文字列になる場合（不正なURL）
    """
    if not url:
        raise ValueError("URL must not be empty.")

    # 1. スキームを除去する
    without_scheme = _SCHEME_PATTERN.sub("", url)

    # 2. すべて小文字化する
    lowered = without_scheme.lower()

    # 3. 英数字以外の文字を _ に置換する
    replaced = _NON_ALNUM_PATTERN.sub("_", lowered)

    # 4. _ の連続を1文字へ圧縮する（_NON_ALNUM_PATTERN の re.sub で既に圧縮済みだが、
    #    連続する記号列（例: "://"）由来の連続 _ を明示的に再度圧縮しておく）
    collapsed = re.sub(r"_+", "_", replaced)

    # 5. 先頭・末尾の _ を除去する
    identifier = collapsed.strip("_")

    if not identifier:
        raise ValueError(f"Failed to generate a valid site_identifier from URL: {url!r}")

    return identifier
