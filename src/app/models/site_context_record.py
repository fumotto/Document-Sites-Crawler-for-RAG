"""サイト単位の処理コンテキストDTO（06_処理シーケンス.md 1.1節）。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.app.models.config_record import ConfigRecord


@dataclass(frozen=True)
class SiteContextRecord:
    site_identifier: str
    base_url: str
    cache_dir: Path
    output_dir: Path
    archive_dir: Path
    manifest_path: Path       # --manifest指定時は上書き。それ以外は cache_dir/manifest.json
    config: ConfigRecord
    started_at: datetime

    @property
    def pages_dir(self) -> Path:
        return self.cache_dir / "pages"

    @property
    def metadata_dir(self) -> Path:
        return self.cache_dir / "metadata"

    @property
    def lock_path(self) -> Path:
        return self.cache_dir / ".lock"
