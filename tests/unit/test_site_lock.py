import os
from pathlib import Path

import pytest

from src.app.exceptions.errors import LockAcquisitionError
from src.app.utils.site_lock import site_lock
import src.app.utils.site_lock as site_lock_module


def assert_readable_and_writable(path: Path) -> None:
    assert os.access(path, os.R_OK)
    assert os.access(path, os.W_OK)


def test_site_lock_creates_readable_file(tmp_path: Path) -> None:
    # TestID: LOCK-001
    lock_path = tmp_path / ".lock"

    with site_lock(lock_path):
        pass

    assert_readable_and_writable(lock_path)


@pytest.mark.skipif(not site_lock_module._HAS_FCNTL, reason="fcntl not available on this platform")
def test_double_acquire_raises_lock_error(tmp_path: Path) -> None:
    # TestID: LOCK-002
    import os as os_module
    import fcntl

    lock_path = tmp_path / ".lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    fd = os_module.open(str(lock_path), os_module.O_CREAT | os_module.O_RDWR, 0o644)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        with pytest.raises(LockAcquisitionError):
            with site_lock(lock_path):
                pass
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os_module.close(fd)


def test_lock_can_be_reacquired_after_release(tmp_path: Path) -> None:
    # TestID: LOCK-003
    lock_path = tmp_path / ".lock"

    with site_lock(lock_path):
        pass

    with site_lock(lock_path):
        pass


def test_lock_released_even_on_exception(tmp_path: Path) -> None:
    # TestID: LOCK-004
    lock_path = tmp_path / ".lock"

    with pytest.raises(RuntimeError):
        with site_lock(lock_path):
            raise RuntimeError("boom")

    # Should be able to re-acquire without issue.
    with site_lock(lock_path):
        pass


def test_pid_based_fallback_lock_when_fcntl_unavailable(tmp_path: Path, monkeypatch) -> None:
    # TestID: LOCK-005
    monkeypatch.setattr(site_lock_module, "_HAS_FCNTL", False)

    lock_path = tmp_path / ".lock"

    with pytest.raises(LockAcquisitionError):
        with site_lock(lock_path):
            with site_lock(lock_path):
                pass


def test_lock_parent_directory_auto_created(tmp_path: Path) -> None:
    # TestID: LOCK-006
    lock_path = tmp_path / "nested" / "dir" / ".lock"

    with site_lock(lock_path):
        pass

    assert lock_path.exists()
    assert lock_path.parent.exists()
