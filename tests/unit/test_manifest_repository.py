import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from datetime import datetime, timezone

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
    repo = ManifestRepository(tmp_path / "manifest.json")
    repo.merge_update("https://example.com/a", _rec(CrawlResult.SUCCESS))
    loaded = repo.load()
    assert loaded["https://example.com/a"].etag == "e1"


def test_network_error_preserves_previous_fields(tmp_path):
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
    repo = ManifestRepository(tmp_path / "manifest.json")
    repo.merge_update("https://example.com/a", _rec(CrawlResult.NOT_MODIFIED))
    loaded = repo.load()
    assert "https://example.com/a" not in loaded


def test_delete_many(tmp_path):
    repo = ManifestRepository(tmp_path / "manifest.json")
    repo.merge_update("https://example.com/a", _rec(CrawlResult.SUCCESS))
    repo.merge_update("https://example.com/b", _rec(CrawlResult.SUCCESS))
    repo.delete_many({"https://example.com/a"})
    loaded = repo.load()
    assert "https://example.com/a" not in loaded
    assert "https://example.com/b" in loaded
