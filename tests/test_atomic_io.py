import stat
from pathlib import Path

from src.app.utils.atomic_io import atomic_write_json, atomic_write_text
from src.app.utils.logging_setup import setup_logging
from src.app.utils.site_lock import site_lock


def test_atomic_write_json_creates_readable_file(tmp_path: Path) -> None:
    output_path = tmp_path / "data.json"

    atomic_write_json(output_path, {"hello": "world"})

    mode = stat.S_IMODE(output_path.stat().st_mode)
    assert mode == 0o644


def test_atomic_write_text_creates_readable_file(tmp_path: Path) -> None:
    output_path = tmp_path / "data.txt"

    atomic_write_text(output_path, "hello")

    mode = stat.S_IMODE(output_path.stat().st_mode)
    assert mode == 0o644


def test_site_lock_creates_readable_file(tmp_path: Path) -> None:
    lock_path = tmp_path / ".lock"

    with site_lock(lock_path):
        pass

    mode = stat.S_IMODE(lock_path.stat().st_mode)
    assert mode == 0o644


def test_setup_logging_creates_readable_file(tmp_path: Path) -> None:
    log_path = tmp_path / "crawler.log"

    setup_logging("INFO", "text", log_path)

    mode = stat.S_IMODE(log_path.stat().st_mode)
    assert mode == 0o644
