import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from unittest.mock import MagicMock, patch

import httpx

# TestID: DIR-001
def test_issue5_tests_dir_not_created(tmp_path):
    """Issue #5: ensure_project_directories() は tests/ を作成しない。"""
    from src.app.utils.directory_bootstrap import ensure_project_directories

    ensure_project_directories(tmp_path)
    created = {p.name for p in tmp_path.iterdir()}
    assert created == {"cache", "output", "archives", "logs"}
    assert "tests" not in created

# TestID: EW-004
def test_issue4_log_level_applied_on_start(monkeypatch, tmp_path):
    """Issue #4: 実行開始時にフォームのlog_levelがルートロガーへ反映される。"""
    import logging

    monkeypatch.setenv("HOME", str(tmp_path))

    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        resp = MagicMock()
        resp.status_code = 404
        resp.headers = {}
        resp.text = ""
        return resp

    from src.app.gui.execution_worker import ExecutionWorker

    logging.getLogger().setLevel(logging.INFO)

    with patch.object(httpx.Client, "get", fake_get):
        worker = ExecutionWorker()
        form = {
            "urls_text": "https://example.com", "mode": "incremental", "word_limit": 450000,
            "request_delay": 0, "include": "", "exclude": "", "max_pages": 1000,
            "timeout_seconds": 5, "log_level": "ERROR",
        }
        worker.start(form)
        assert logging.getLogger().level == logging.ERROR

        for _ in range(50):
            if worker.get_state_snapshot().state != "running":
                break
            time.sleep(0.1)

# TestID: ISS6-001
def test_issue6_implicit_include_from_path(tmp_path):
    """Issue #6: INCLUDE未設定時、対象URLのパスが暗黙のスコープになる。"""
    from src.app.crawler.crawler_service import CrawlerService
    from src.app.models.config_record import ConfigRecord
    from src.app.repository.manifest_repository import ManifestRepository
    from src.app.repository.page_metadata_repository import PageMetadataRepository
    from src.app.repository.page_repository import PageRepository

    pages = {
        "https://supabase.com/docs/guides":
            "<html><head><title>Guides</title></head><body><p>guides content</p></body></html>",
    }

    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        resp = MagicMock()
        if url.endswith("robots.txt"):
            resp.status_code = 200
            resp.text = "User-agent: *\nAllow: /\nSitemap: https://supabase.com/sitemap.xml"
            return resp
        if url.endswith("sitemap.xml"):
            resp.status_code = 200
            resp.content = b"""<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://supabase.com/docs/guides</loc></url>
  <url><loc>https://supabase.com/alternatives/</loc></url>
  <url><loc>https://supabase.com/blog/</loc></url>
</urlset>"""
            return resp
        if url in pages:
            resp.status_code = 200
            resp.headers = {"Content-Type": "text/html"}
            resp.text = pages[url]
            return resp
        resp.status_code = 404
        resp.headers = {}
        return resp

    config = ConfigRecord(
        url="https://supabase.com/docs/guides", base_urls=[], manifest_path_override=None,
        mode="incremental", word_limit=450000, request_delay=0, user_agent="test",
        include=[], exclude=[], max_pages=1000, timeout_seconds=10,
    )
    manifest_repo = ManifestRepository(tmp_path / "manifest.json")
    page_repo = PageRepository(tmp_path / "pages")
    meta_repo = PageMetadataRepository(tmp_path / "metadata")

    with patch.object(httpx.Client, "get", fake_get):
        service = CrawlerService(manifest_repo, page_repo, meta_repo, config)
        outcome = service.process_site("https://supabase.com/docs/guides")

    crawled_urls = {r.url for r in outcome.page_results}
    assert crawled_urls == {"https://supabase.com/docs/guides"}

# TestID: ISS6-002
def test_issue6_explicit_include_still_takes_priority(tmp_path):
    """Issue #6: INCLUDEが明示指定されている場合はそちらを優先する（CLI互換性維持）。"""
    from src.app.crawler.crawler_service import CrawlerService
    from src.app.models.config_record import ConfigRecord
    from src.app.repository.manifest_repository import ManifestRepository
    from src.app.repository.page_metadata_repository import PageMetadataRepository
    from src.app.repository.page_repository import PageRepository

    pages = {
        "https://supabase.com/docs/guides":
            "<html><head><title>Guides</title></head><body><p>guides</p></body></html>",
        "https://supabase.com/blog/x":
            "<html><head><title>Blog</title></head><body><p>blog</p></body></html>",
    }

    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        resp = MagicMock()
        if url.endswith("robots.txt"):
            resp.status_code = 200
            resp.text = "User-agent: *\nAllow: /\nSitemap: https://supabase.com/sitemap.xml"
            return resp
        if url.endswith("sitemap.xml"):
            resp.status_code = 200
            resp.content = b"""<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://supabase.com/docs/guides</loc></url>
  <url><loc>https://supabase.com/blog/x</loc></url>
</urlset>"""
            return resp
        if url in pages:
            resp.status_code = 200
            resp.headers = {"Content-Type": "text/html"}
            resp.text = pages[url]
            return resp
        resp.status_code = 404
        resp.headers = {}
        return resp

    # INCLUDEに明示的に "/blog" を指定 -> パスからの暗黙スコープ(/docs/guides)より優先されるはず
    config = ConfigRecord(
        url="https://supabase.com/docs/guides", base_urls=[], manifest_path_override=None,
        mode="incremental", word_limit=450000, request_delay=0, user_agent="test",
        include=["/blog"], exclude=[], max_pages=1000, timeout_seconds=10,
    )
    manifest_repo = ManifestRepository(tmp_path / "manifest.json")
    page_repo = PageRepository(tmp_path / "pages")
    meta_repo = PageMetadataRepository(tmp_path / "metadata")

    with patch.object(httpx.Client, "get", fake_get):
        service = CrawlerService(manifest_repo, page_repo, meta_repo, config)
        outcome = service.process_site("https://supabase.com/docs/guides")

    crawled_urls = {r.url for r in outcome.page_results}
    assert crawled_urls == {"https://supabase.com/blog/x"}
