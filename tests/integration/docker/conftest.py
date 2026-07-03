import shutil
from pathlib import Path

import pytest

TEST_ROOT = Path(__file__).resolve().parent
TEST_WORKSPACE = TEST_ROOT / ".test-workspace"


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_workspace():
    if TEST_WORKSPACE.exists():
        shutil.rmtree(TEST_WORKSPACE)
    yield
    if TEST_WORKSPACE.exists():
        shutil.rmtree(TEST_WORKSPACE)


@pytest.fixture(scope="session")
def test_workspace_path():
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    yield TEST_WORKSPACE
