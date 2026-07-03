import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from unittest.mock import MagicMock, patch

import httpx

from src.app.gui.execution_worker import ExecutionWorker, STATE_FAILED, STATE_IDLE, STATE_RUNNING
from src.app.gui.js_api import JsApi
from src.app.gui.log_buffer import InMemoryLogHandler

# TestID: EW-001
def test_initial_state_is_idle():
    worker = ExecutionWorker()
    assert worker.get_state_snapshot().state == STATE_IDLE
    assert not worker.is_running

# TestID: EW-002
def test_invalid_form_transitions_to_failed_without_thread(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    worker = ExecutionWorker()
    worker.start({"urls_text": ""})  # 空URL -> ConfigError
    state = worker.get_state_snapshot()
    assert state.state == STATE_FAILED
    assert state.error_message

# TestID: EW-003
def test_double_start_is_ignored_while_running(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))

    def slow_get(self, url, timeout=None, headers=None, allow_redirects=None):
        time.sleep(0.3)
        resp = MagicMock()
        resp.status_code = 404
        resp.headers = {}
        resp.text = ""
        return resp

    with patch.object(httpx.Client, "get", slow_get):
        worker = ExecutionWorker()
        form = {
            "urls_text": "https://example.com", "mode": "incremental", "word_limit": 450000,
            "request_delay": 0, "include": "", "exclude": "", "max_pages": 1000,
            "timeout_seconds": 5, "log_level": "INFO",
        }
        worker.start(form)
        assert worker.is_running
        worker.start(form)  # 二重実行は無視される
        assert worker.is_running

        for _ in range(50):
            if not worker.is_running:
                break
            time.sleep(0.1)

# TestID: JSAPI-001
def test_js_api_get_status_returns_diff_only():
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

# TestID: JSAPI-002
def test_js_api_already_running_response(monkeypatch, tmp_path):
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
