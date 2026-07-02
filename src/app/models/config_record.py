"""実行時設定DTO（07_CLI仕様.md 3節の環境変数一覧に対応）。"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class ConfigRecord:
    # 対象URL（単一サイト処理時）。複数サイト処理時は None とし base_urls を使用する。
    url: Optional[str]
    base_urls: List[str] = field(default_factory=list)

    # --manifest によるmanifest.json保存先の上書き（単一サイト処理時のみ許可）
    manifest_path_override: Optional[Path] = None

    mode: str = "incremental"                 # "incremental" | "full"
    word_limit: int = 450_000
    request_delay: float = 0.5
    user_agent: str = "NotebookLM-Crawler/1.0"
    include: List[str] = field(default_factory=list)
    exclude: List[str] = field(default_factory=list)
    max_pages: int = 1000
    timeout_seconds: int = 30

    log_level: str = "INFO"
    log_format: str = "text"                  # "text" | "json"
    log_file_path: Path = Path("logs/crawler.log")

    @property
    def is_multi_site(self) -> bool:
        """複数サイト処理（BASE_URLS経由）かどうかを判定する（07_CLI仕様 5節）。"""
        return self.url is None and bool(self.base_urls)
