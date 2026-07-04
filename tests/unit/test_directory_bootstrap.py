from datetime import datetime, timezone
from pathlib import Path

from src.app.models.config_record import ConfigRecord
from src.app.utils.directory_bootstrap import build_site_context, ensure_project_directories


def test_issue5_tests_dir_not_created(tmp_path: Path) -> None:
    # TestID: DIR-001
    ensure_project_directories(tmp_path)
    created = {p.name for p in tmp_path.iterdir()}
    assert created == {"cache", "output", "archives", "logs"}
    assert "tests" not in created


def _config(**overrides):
    base = dict(
        url="https://example.com/docs", base_urls=[], manifest_path_override=None,
        mode="incremental", word_limit=450000, request_delay=0.5, user_agent="test",
        include=[], exclude=[], max_pages=1000, timeout_seconds=30,
    )
    base.update(overrides)
    return ConfigRecord(**base)


def test_build_site_context_creates_per_site_directories(tmp_path: Path) -> None:
    # TestID: DIR-002
    config = _config()

    ctx = build_site_context("https://example.com/docs", config, root=tmp_path)

    assert ctx.pages_dir.exists()
    assert ctx.metadata_dir.exists()
    assert ctx.output_dir.exists()
    assert ctx.archive_dir.exists()


def test_manifest_path_override_applied(tmp_path: Path) -> None:
    # TestID: DIR-003
    override_path = tmp_path / "custom-manifest.json"
    config = _config(manifest_path_override=override_path)

    ctx = build_site_context("https://example.com/docs", config, root=tmp_path)

    assert ctx.manifest_path == override_path


def test_ensure_project_directories_idempotent(tmp_path: Path) -> None:
    # TestID: DIR-004
    ensure_project_directories(tmp_path)
    ensure_project_directories(tmp_path)  # should not raise
    assert (tmp_path / "cache").exists()


def test_site_context_record_fields_match_expected_paths(tmp_path: Path) -> None:
    # TestID: DIR-005
    config = _config()

    before = datetime.now(timezone.utc)
    ctx = build_site_context("https://example.com/docs", config, root=tmp_path)
    after = datetime.now(timezone.utc)

    assert ctx.site_identifier == "example_com_docs"
    assert ctx.cache_dir == tmp_path / "cache" / "example_com_docs"
    assert ctx.output_dir == tmp_path / "output" / "example_com_docs"
    assert ctx.archive_dir == tmp_path / "archives" / "example_com_docs"
    assert ctx.manifest_path == ctx.cache_dir / "manifest.json"
    assert ctx.started_at.tzinfo is not None
    assert before <= ctx.started_at <= after
