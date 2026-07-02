"""クロール結果種別（05_データ構造設計.md 参照）。"""
from __future__ import annotations

from enum import Enum


class CrawlResult(str, Enum):
    SUCCESS = "SUCCESS"
    NOT_MODIFIED = "NOT_MODIFIED"
    NOT_FOUND = "NOT_FOUND"
    ROBOTS_DENIED = "ROBOTS_DENIED"
    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT = "TIMEOUT"
    SERVER_ERROR = "SERVER_ERROR"
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"
