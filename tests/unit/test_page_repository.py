import pytest

from src.app.repository.page_repository import PageRepository


def test_save_then_load_page_round_trip(tmp_path):
    # TestID: PR-001
    repo = PageRepository(tmp_path)

    repo.save("hash1", "# Hello\nBody content.")
    loaded = repo.load_page("hash1")

    assert loaded == "# Hello\nBody content."


def test_load_page_raises_for_missing_hash(tmp_path):
    # TestID: PR-002
    repo = PageRepository(tmp_path)

    with pytest.raises(FileNotFoundError):
        repo.load_page("does-not-exist")


def test_exists_reflects_file_presence(tmp_path):
    # TestID: PR-003
    repo = PageRepository(tmp_path)
    repo.save("hash1", "body")

    assert repo.exists("hash1") is True
    assert repo.exists("hash2") is False


def test_delete_removes_file(tmp_path):
    # TestID: PR-004
    repo = PageRepository(tmp_path)
    repo.save("hash1", "body")

    repo.delete("hash1")

    assert repo.exists("hash1") is False
