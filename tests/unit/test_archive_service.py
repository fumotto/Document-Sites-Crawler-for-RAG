import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from src.app.archive.archive_service import ArchiveService
from src.app.models.config_record import ConfigRecord
from src.app.models.site_context_record import SiteContextRecord


def _site_context(tmp_path):
    config = ConfigRecord(
        url="https://example.com", base_urls=[], manifest_path_override=None,
        mode="incremental", word_limit=450000, request_delay=0, user_agent="test",
        include=[], exclude=[], max_pages=1000, timeout_seconds=10,
    )
    cache_dir = tmp_path / "cache" / "site"
    output_dir = tmp_path / "output" / "site"
    archive_dir = tmp_path / "archives" / "site"
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    return SiteContextRecord(
        site_identifier="site", base_url="https://example.com", cache_dir=cache_dir,
        output_dir=output_dir, archive_dir=archive_dir,
        manifest_path=cache_dir / "manifest.json", config=config,
        started_at=datetime.now(timezone.utc),
    )


def test_output_files_included_in_zip(tmp_path):
    # TestID: ARC-001
    ctx = _site_context(tmp_path)
    (ctx.output_dir / "docs_001.md").write_text("content a", encoding="utf-8")
    (ctx.output_dir / "Index.md").write_text("index content", encoding="utf-8")

    service = ArchiveService()
    archive_path = service.archive(ctx)

    with zipfile.ZipFile(archive_path) as zf:
        names = set(zf.namelist())
    assert names == {"docs_001.md", "Index.md"}


def test_archive_filename_matches_naming_convention(tmp_path):
    # TestID: ARC-002
    ctx = _site_context(tmp_path)
    (ctx.output_dir / "docs_001.md").write_text("content", encoding="utf-8")

    service = ArchiveService()
    archive_path = service.archive(ctx)

    filename = Path(archive_path).name
    assert filename.startswith("site_")
    assert filename.endswith(".zip")
    # site_YYYYMMDD_HHMMSS.zip -> the middle segment should be 15 chars: 8 + '_' + 6
    timestamp_part = filename[len("site_"):-len(".zip")]
    assert len(timestamp_part) == 15


def test_repeated_archive_calls_produce_distinct_files(tmp_path):
    # TestID: ARC-003
    ctx = _site_context(tmp_path)
    (ctx.output_dir / "docs_001.md").write_text("content", encoding="utf-8")

    service = ArchiveService()
    first_path = service.archive(ctx)
    time.sleep(1.1)  # ensure a different second-level timestamp
    second_path = service.archive(ctx)

    assert first_path != second_path
    assert Path(first_path).exists()
    assert Path(second_path).exists()


def test_empty_output_dir_produces_empty_zip_without_error(tmp_path):
    # TestID: ARC-004
    ctx = _site_context(tmp_path)  # output_dir created but left empty

    service = ArchiveService()
    archive_path = service.archive(ctx)

    with zipfile.ZipFile(archive_path) as zf:
        assert zf.namelist() == []
