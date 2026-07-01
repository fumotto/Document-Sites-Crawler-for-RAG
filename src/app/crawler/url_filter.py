"""URLフィルタ（要件定義書11節）。INCLUDE/EXCLUDEパスによる対象URLの絞り込み。"""
from __future__ import annotations

from typing import List
from urllib.parse import urlsplit


def is_included(url: str, include: List[str], exclude: List[str]) -> bool:
    path = urlsplit(url).path

    if exclude and any(path.startswith(pattern) for pattern in exclude):
        return False

    if include:
        return any(path.startswith(pattern) for pattern in include)

    return True
