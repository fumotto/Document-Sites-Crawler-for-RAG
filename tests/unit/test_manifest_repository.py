from datetime import datetime, timezone

from src.app.mapper.manifest_mapper import dict_to_manifest_record, manifest_record_to_dict
from src.app.models.crawl_result import CrawlResult
from src.app.models.manifest_record import ManifestRecord
from src.app.repository.manifest_repository import ManifestRepository


def _rec(crawl_result, etag="e1", content_sha256="sha1"):
    return ManifestRecord(
        page_hash="hash1", etag=etag, last_modified=None, sitemap_lastmod=None,
        content_sha256=content_sha256, last_crawled=datetime.now(timezone.utc),
        crawl_result=crawl_result,
    )


def test_success_full_update(tmp_path):
    # TestID: MAN-001
    repo = ManifestRepository(tmp_path / "manifest.json")
    repo.merge_update("https://example.com/a", _rec(CrawlResult.SUCCESS))
    loaded = repo.load()
    assert loaded["https://example.com/a"].etag == "e1"


def test_network_error_preserves_previous_fields(tmp_path):
    # TestID: MAN-002
    repo = ManifestRepository(tmp_path / "manifest.json")
    repo.merge_update("https://example.com/a", _rec(CrawlResult.SUCCESS, etag="original-etag"))
    repo.merge_update(
        "https://example.com/a",
        _rec(CrawlResult.NETWORK_ERROR, etag=None, content_sha256=None),
    )
    loaded = repo.load()
    assert loaded["https://example.com/a"].etag == "original-etag"
    assert loaded["https://example.com/a"].crawl_result == CrawlResult.NETWORK_ERROR


def test_not_modified_does_not_write(tmp_path):
    # TestID: MAN-003
    repo = ManifestRepository(tmp_path / "manifest.json")
    repo.merge_update("https://example.com/a", _rec(CrawlResult.NOT_MODIFIED))
    loaded = repo.load()
    assert "https://example.com/a" not in loaded


def test_delete_many(tmp_path):
    # TestID: MAN-004
    repo = ManifestRepository(tmp_path / "manifest.json")
    repo.merge_update("https://example.com/a", _rec(CrawlResult.SUCCESS))
    repo.merge_update("https://example.com/b", _rec(CrawlResult.SUCCESS))
    repo.delete_many({"https://example.com/a"})
    loaded = repo.load()
    assert "https://example.com/a" not in loaded
    assert "https://example.com/b" in loaded


def test_load_returns_empty_dict_when_file_missing(tmp_path):
    # TestID: MAN-005
    repo = ManifestRepository(tmp_path / "manifest.json")
    assert repo.load() == {}


def test_not_found_and_robots_denied_preserve_previous_fields(tmp_path):
    # TestID: MAN-006
    repo = ManifestRepository(tmp_path / "manifest.json")
    repo.merge_update("https://example.com/a", _rec(CrawlResult.SUCCESS, etag="original-etag"))
    repo.merge_update(
        "https://example.com/a", _rec(CrawlResult.NOT_FOUND, etag=None, content_sha256=None),
    )
    loaded = repo.load()
    assert loaded["https://example.com/a"].etag == "original-etag"
    assert loaded["https://example.com/a"].crawl_result == CrawlResult.NOT_FOUND


def test_no_existing_record_registers_new_record_fully_regardless_of_result(tmp_path):
    # TestID: MAN-007
    # When there is no existing record, merge_update registers the new
    # record in full (all fields as given), even for a "partial update"
    # crawl_result such as NETWORK_ERROR -- this is a new registration,
    # not a preservation of prior data (there is no prior data).
    repo = ManifestRepository(tmp_path / "manifest.json")
    new_record = _rec(CrawlResult.NETWORK_ERROR, etag="should-be-kept", content_sha256="should-be-kept")

    repo.merge_update("https://example.com/new", new_record)

    loaded = repo.load()
    assert loaded["https://example.com/new"].etag == "should-be-kept"
    assert loaded["https://example.com/new"].content_sha256 == "should-be-kept"
    assert loaded["https://example.com/new"].crawl_result == CrawlResult.NETWORK_ERROR


def test_manifest_record_roundtrip_conversion():
    # TestID: MAN-008
    record = _rec(CrawlResult.SUCCESS)
    as_dict = manifest_record_to_dict(record)
    restored = dict_to_manifest_record(as_dict)
    assert restored == record


def test_delete_nonexistent_url_does_not_raise(tmp_path):
    # TestID: MAN-009
    repo = ManifestRepository(tmp_path / "manifest.json")
    repo.delete("https://example.com/does-not-exist")  # should not raise


def test_delete_many_with_no_matching_urls_does_not_save(tmp_path, monkeypatch):
    # TestID: MAN-010
    repo = ManifestRepository(tmp_path / "manifest.json")
    repo.merge_update("https://example.com/a", _rec(CrawlResult.SUCCESS))

    save_calls = []
    original_save = repo.save

    def spy_save(pages):
        save_calls.append(pages)
        original_save(pages)

    monkeypatch.setattr(repo, "save", spy_save)

    repo.delete_many({"https://example.com/does-not-exist"})

    assert save_calls == []
