"""
URL正規化ユーティリティ。

要件定義書7節「クロール時のURL正規化ルール」に基づき、URLを正規化する。
正規化後URLは manifest.json のキー、および page_hash（SHA-256）の算出元として使用する
（05_データ構造設計.md 参照）。

正規化ルール:
    - スキーム・ホスト名を小文字化する
    - デフォルトポート（http:80 / https:443）を除去する
    - フラグメント（#...）を除去する
    - 末尾スラッシュの有無は正規化しない（page側の責務ではなく、
      サイト識別子生成のみ末尾スラッシュを同一視する。ページ単位のURLは
      末尾スラッシュの有無をそのまま保持することで、異なるページを
      誤って同一視しないようにする）
"""
from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

_DEFAULT_PORTS = {"http": 80, "https": 443}


def normalize_url(url: str) -> str:
    """URLを正規化する。

    Args:
        url: 正規化対象のURL

    Returns:
        正規化済みURL
    """
    parts = urlsplit(url)

    scheme = parts.scheme.lower()
    hostname = (parts.hostname or "").lower()

    port = parts.port
    if port is not None and _DEFAULT_PORTS.get(scheme) == port:
        port = None

    netloc = hostname
    if port is not None:
        netloc = f"{hostname}:{port}"

    if parts.username:
        userinfo = parts.username
        if parts.password:
            userinfo += f":{parts.password}"
        netloc = f"{userinfo}@{netloc}"

    # フラグメントは除去する。クエリはページを区別しうるため保持する。
    normalized = urlunsplit((scheme, netloc, parts.path or "/", parts.query, ""))
    return normalized


def compute_page_hash(normalized_url: str) -> str:
    """正規化後URLからpage_hash（SHA-256）を算出する（05_データ構造設計.md）。"""
    import hashlib

    return hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()
