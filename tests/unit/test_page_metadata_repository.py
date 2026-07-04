from datetime import datetime, timezone

from src.app.mapper.page_metadata_mapper import dict_to_page_metadata
from src.app.models.page_metadata_record import PageMetadataRecord
from src.app.repository.page_metadata_repository import PageMetadataRepository


def _meta(url="https://example.com/a"):
    return PageMetadataRecord(
        title="T", url=url, language="en", word_count=10, char_count=50,
        token_count=12, content_sha256="sha", retrieved_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        content_type="text/html",
    )


def test_save_then_load_round_trip(tmp_path):
    # TestID: PM-001
    repo = PageMetadataRepository(tmp_path)
    record = _meta()

    repo.save("hash1", record)
    loaded = repo.load("hash1")

    assert loaded == record


def test_exists_reflects_file_presence(tmp_path):
    # TestID: PM-002
    repo = PageMetadataRepository(tmp_path)
    repo.save("hash1", _meta())

    assert repo.exists("hash1") is True
    assert repo.exists("hash2") is False


def test_delete_removes_file(tmp_path):
    # TestID: PM-003
    repo = PageMetadataRepository(tmp_path)
    repo.save("hash1", _meta())

    repo.delete("hash1")

    assert repo.exists("hash1") is False


def test_load_all_returns_all_records_as_tuples(tmp_path):
    # TestID: PM-004
    repo = PageMetadataRepository(tmp_path)
    repo.save("hash1", _meta("https://example.com/a"))
    repo.save("hash2", _meta("https://example.com/b"))

    results = repo.load_all()

    hashes = {h for h, _r in results}
    urls = {r.url for _h, r in results}
    assert hashes == {"hash1", "hash2"}
    assert urls == {"https://example.com/a", "https://example.com/b"}


def test_load_all_returns_empty_list_when_directory_missing(tmp_path):
    # TestID: PM-005
    missing_dir = tmp_path / "does-not-exist"
    repo = PageMetadataRepository(missing_dir)

    assert repo.load_all() == []


def test_dict_to_page_metadata_parses_datetime_correctly():
    # TestID: PM-006
    data = {
        "title": "T", "url": "https://example.com/a", "language": "en",
        "word_count": 10, "char_count": 50, "token_count": 12,
        "content_sha256": "sha", "retrieved_at": "2026-01-01T00:00:00+00:00",
        "content_type": "text/html",
    }

    record = dict_to_page_metadata(data)

    assert record.retrieved_at == datetime(2026, 1, 1, tzinfo=timezone.utc)
