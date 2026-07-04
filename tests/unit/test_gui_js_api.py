import time
from unittest.mock import MagicMock, patch

import httpx

from src.app.gui import js_api as js_api_module
from src.app.gui.js_api import JsApi
from src.app.gui.log_buffer import InMemoryLogHandler


def test_js_api_get_status_returns_diff_only():
    # TestID: JSAPI-001
    handler = InMemoryLogHandler()
    api = JsApi(handler)

    import logging

    logger = logging.getLogger("test_js_api")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    logger.info("line1")
    logger.info("line2")

    status1 = api.get_status(since_index=-1)
    assert status1["log_lines"] == ["line1", "line2"]
    assert status1["last_index"] == 1

    logger.info("line3")
    status2 = api.get_status(since_index=status1["last_index"])
    assert status2["log_lines"] == ["line3"]


def test_js_api_already_running_response(monkeypatch, tmp_path):
    # TestID: JSAPI-002
    monkeypatch.setenv("HOME", str(tmp_path))

    def slow_get(self, url, timeout=None, headers=None, allow_redirects=None):
        time.sleep(0.3)
        resp = MagicMock()
        resp.status_code = 404
        resp.headers = {}
        resp.text = ""
        return resp

    handler = InMemoryLogHandler()
    api = JsApi(handler)
    form = {
        "urls_text": "https://example.com", "mode": "incremental", "word_limit": 450000,
        "request_delay": 0, "include": "", "exclude": "", "max_pages": 1000,
        "timeout_seconds": 5, "log_level": "INFO",
    }
    with patch.object(httpx.Client, "get", slow_get):
        r1 = api.start_execution(form)
        assert r1["status"] == "started"
        r2 = api.start_execution(form)
        assert r2["status"] == "already_running"

        for _ in range(50):
            if not api._worker.is_running:
                break
            time.sleep(0.1)


def test_load_settings_returns_settings_store_value(monkeypatch, tmp_path):
    # TestID: JSAPI-003
    handler = InMemoryLogHandler()
    api = JsApi(handler)

    fake_settings = {"urls_text": "https://from-store.com"}
    monkeypatch.setattr(js_api_module, "load_settings", lambda: fake_settings)

    result = api.load_settings()

    assert result == fake_settings


def test_get_app_info_returns_app_name_and_version():
    # TestID: JSAPI-004
    handler = InMemoryLogHandler()
    api = JsApi(handler)

    from src.app.gui import app_version

    info = api.get_app_info()

    assert info["app_name"] == app_version.APP_NAME
    assert info["version"] == app_version.APP_VERSION


def test_open_log_folder_returns_error_status_on_exception(monkeypatch):
    # TestID: JSAPI-005
    handler = InMemoryLogHandler()
    api = JsApi(handler)

    def raising_run(*args, **kwargs):
        raise OSError("cannot open folder")

    monkeypatch.setattr(js_api_module.subprocess, "run", raising_run)

    result = api.open_log_folder()

    assert result["status"] == "error"
    assert "message" in result


def test_start_execution_saves_settings(monkeypatch, tmp_path):
    # TestID: JSAPI-006
    monkeypatch.setenv("HOME", str(tmp_path))
    handler = InMemoryLogHandler()
    api = JsApi(handler)

    saved = {}

    def fake_save_settings(form_data):
        saved.update(form_data)

    monkeypatch.setattr(js_api_module, "save_settings", fake_save_settings)

    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        resp = MagicMock()
        resp.status_code = 404
        resp.headers = {}
        resp.text = ""
        return resp

    form = {
        "urls_text": "https://example.com", "mode": "incremental", "word_limit": 450000,
        "request_delay": 0, "include": "", "exclude": "", "max_pages": 1000,
        "timeout_seconds": 5, "log_level": "INFO",
    }

    with patch.object(httpx.Client, "get", fake_get):
        api.start_execution(form)
        for _ in range(50):
            if not api._worker.is_running:
                break
            time.sleep(0.1)

    assert saved.get("urls_text") == "https://example.com"
