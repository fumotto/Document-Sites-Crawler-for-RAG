import os
import pytest
from pathlib import Path

from src.app.utils.atomic_io import atomic_write_json, atomic_write_text
from src.app.utils.logging_setup import setup_logging
from src.app.utils.site_lock import site_lock


def assert_readable_and_writable(path: Path) -> None:
    assert os.access(path, os.R_OK)
    assert os.access(path, os.W_OK)


# TestID: AT-001
def test_atomic_write_json_creates_readable_file(self, tmp_path: Path) -> None:
    output_path = tmp_path / "data.json"

    atomic_write_json(output_path, {"hello": "world"})

    assert_readable_and_writable(output_path)


# TestID: AT-002
def test_atomic_write_text_creates_readable_file(self, tmp_path: Path) -> None:
    output_path = tmp_path / "data.txt"

    atomic_write_text(output_path, "hello")

    assert_readable_and_writable(output_path)

# TestID: LOCK-001
def test_site_lock_creates_readable_file(self, tmp_path: Path) -> None:
    lock_path = tmp_path / ".lock"

    with site_lock(lock_path):
        pass

    assert_readable_and_writable(lock_path)

# TestID: LOG-001
def test_setup_logging_creates_readable_file(self, tmp_path: Path) -> None:
    log_path = tmp_path / "crawler.log"

    setup_logging("INFO", "text", log_path)

    assert_readable_and_writable(log_path)
