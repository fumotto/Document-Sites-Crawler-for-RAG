import pytest
from pathlib import Path

from test_tools.testspace_utils import clean_test_workspace

TEST_ROOT = Path(__file__).resolve().parent
TEST_WORKSPACE = TEST_ROOT / ".test-workspace"


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_workspace():
    if TEST_WORKSPACE.exists():
        clean_test_workspace()
    yield
    if TEST_WORKSPACE.exists():
        clean_test_workspace()


@pytest.fixture(scope="session")
def test_workspace_path():
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    yield TEST_WORKSPACE
