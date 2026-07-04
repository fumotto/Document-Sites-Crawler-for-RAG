from src.app.mapper.chunk_mapper import chunk_records_to_list, list_to_chunk_records
from src.app.models.chunk_record import ChunkRecord
from src.app.repository.chunk_manifest_repository import ChunkManifestRepository


def _record(url="https://example.com/a"):
    return ChunkRecord(title="T", url=url, file="docs_001.md", sha256="sha", word_count=100)


def test_save_then_load_round_trip(tmp_path):
    # TestID: CM-001
    repo = ChunkManifestRepository(tmp_path)
    records = [_record("https://example.com/a"), _record("https://example.com/b")]

    repo.save(records)
    loaded = repo.load()

    assert loaded == records


def test_load_returns_empty_list_when_file_missing(tmp_path):
    # TestID: CM-002
    repo = ChunkManifestRepository(tmp_path)

    assert repo.load() == []


def test_chunk_records_to_list_and_back_round_trip():
    # TestID: CM-003
    records = [_record("https://example.com/a"), _record("https://example.com/b")]

    as_list = chunk_records_to_list(records)
    restored = list_to_chunk_records(as_list)

    assert restored == records


def test_chunk_manifest_repository_save_load_cycle_with_multiple_records(tmp_path):
    # TestID: CM-004
    # Confirms the Repository layer (not just the Mapper) persists and
    # restores data correctly end-to-end via the actual file on disk.
    repo = ChunkManifestRepository(tmp_path)
    records = [
        _record("https://example.com/a"),
        _record("https://example.com/b"),
        _record("https://example.com/c"),
    ]

    repo.save(records)

    # Simulate a fresh process by constructing a new repository instance
    # pointed at the same directory.
    fresh_repo = ChunkManifestRepository(tmp_path)
    loaded = fresh_repo.load()

    assert loaded == records
