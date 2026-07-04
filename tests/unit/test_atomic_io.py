import os
from pathlib import Path

import pytest

from src.app.utils.atomic_io import atomic_write_json, atomic_write_text, read_json, _atomic_write


def assert_readable_and_writable(path: Path) -> None:
    assert os.access(path, os.R_OK)
    assert os.access(path, os.W_OK)


def test_atomic_write_json_creates_readable_file(tmp_path: Path) -> None:
    # TestID: AIO-001
    output_path = tmp_path / "data.json"

    atomic_write_json(output_path, {"hello": "world"})

    assert_readable_and_writable(output_path)


def test_atomic_write_text_creates_readable_file(tmp_path: Path) -> None:
    # TestID: AIO-002
    output_path = tmp_path / "data.txt"

    atomic_write_text(output_path, "hello")

    assert_readable_and_writable(output_path)


def test_read_json_round_trip(tmp_path: Path) -> None:
    # TestID: AIO-003
    output_path = tmp_path / "data.json"
    original = {"hello": "world", "n": 1}

    atomic_write_json(output_path, original)
    loaded = read_json(output_path)

    assert loaded == original


def test_overwrite_existing_file(tmp_path: Path) -> None:
    # TestID: AIO-004
    output_path = tmp_path / "data.json"

    atomic_write_json(output_path, {"v": 1})
    atomic_write_json(output_path, {"v": 2})

    assert read_json(output_path) == {"v": 2}


def test_parent_directory_auto_created(tmp_path: Path) -> None:
    # TestID: AIO-005
    output_path = tmp_path / "nested" / "dir" / "data.json"

    atomic_write_json(output_path, {"v": 1})

    assert output_path.exists()
    assert output_path.parent.exists()


def test_no_tmp_file_left_on_writer_exception(tmp_path: Path) -> None:
    # TestID: AIO-006
    output_path = tmp_path / "data.json"

    def failing_writer(f):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        _atomic_write(output_path, failing_writer)

    leftover = list(tmp_path.glob(".*.tmp"))
    assert leftover == []


def test_fchmod_failure_is_swallowed(tmp_path: Path, monkeypatch) -> None:
    # TestID: AIO-007
    import src.app.utils.atomic_io as atomic_io_module

    def failing_fchmod(fd, mode):
        raise PermissionError("no fchmod on this platform")

    monkeypatch.setattr(atomic_io_module.os, "fchmod", failing_fchmod)

    output_path = tmp_path / "data.json"
    atomic_write_json(output_path, {"v": 1})

    assert read_json(output_path) == {"v": 1}
