"""ディレクトリ構造の自動生成ロジック（03_ディレクトリ構成.md）。"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.app.models.config_record import ConfigRecord
from src.app.models.site_context_record import SiteContextRecord
from src.app.utils.site_identifier import generate_site_identifier

PROJECT_ROOT = Path(".")


def ensure_project_directories(root: Path = PROJECT_ROOT) -> None:
    """cache/, output/, archives/, logs/, tests/ を作成する（03節）。"""
    for name in ("cache", "output", "archives", "logs", "tests"):
        (root / name).mkdir(parents=True, exist_ok=True)


def build_site_context(base_url: str, config: ConfigRecord, root: Path = PROJECT_ROOT) -> SiteContextRecord:
    """指定URLに対応する SiteContextRecord を生成し、必要なディレクトリを作成する。"""
    site_identifier = generate_site_identifier(base_url)

    cache_dir = root / "cache" / site_identifier
    output_dir = root / "output" / site_identifier
    archive_dir = root / "archives" / site_identifier

    (cache_dir / "pages").mkdir(parents=True, exist_ok=True)
    (cache_dir / "metadata").mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = config.manifest_path_override or (cache_dir / "manifest.json")

    return SiteContextRecord(
        site_identifier=site_identifier,
        base_url=base_url,
        cache_dir=cache_dir,
        output_dir=output_dir,
        archive_dir=archive_dir,
        manifest_path=manifest_path,
        config=config,
        started_at=datetime.now(timezone.utc),
    )
