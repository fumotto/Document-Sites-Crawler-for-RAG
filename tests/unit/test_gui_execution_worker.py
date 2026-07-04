import time
from unittest.mock import MagicMock, patch

import httpx

from src.app.gui.execution_worker import ExecutionWorker, STATE_COMPLETED, STATE_FAILED, STATE_IDLE, STATE_RUNNING
from src.app.gui.js_api import JsApi
from src.app.gui.log_buffer import InMemoryLogHandler


def test_initial_state_is_idle():
    # TestID: EW-001
    worker = ExecutionWorker()
    assert worker.get_state_snapshot().state == STATE_IDLE
    assert not worker.is_running


def test_invalid_form_transitions_to_failed_without_thread(monkeypatch, tmp_path):
    # TestID: EW-002
    monkeypatch.setenv("HOME", str(tmp_path))
    worker = ExecutionWorker()
    worker.start({"urls_text": ""})  # invalid: empty URL -> ConfigError
    state = worker.get_state_snapshot()
    assert state.state == STATE_FAILED
    assert state.error_message


def test_double_start_is_ignored_while_running(monkeypatch, tmp_path):
    # TestID: EW-003
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
        worker.start(form)  # should be ignored while running
        assert worker.is_running

        for _ in range(50):
            if not worker.is_running:
                break
            time.sleep(0.1)


def test_issue4_log_level_applied_on_start(monkeypatch, tmp_path):
    # TestID: EW-004
    import logging

    monkeypatch.setenv("HOME", str(tmp_path))

    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        resp = MagicMock()
        resp.status_code = 404
        resp.headers = {}
        resp.text = ""
        return resp

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


def test_execution_completes_with_result_summary(monkeypatch, tmp_path):
    # TestID: EW-005
    monkeypatch.setenv("HOME", str(tmp_path))

    def fake_get(self, url, timeout=None, headers=None, follow_redirects=None):
        resp = MagicMock()
        resp.status_code = 404
        resp.headers = {}
        resp.text = ""
        return resp

    with patch.object(httpx.Client, "get", fake_get):
        worker = ExecutionWorker()
        form = {
            "urls_text": "https://example.com", "mode": "incremental", "word_limit": 450000,
            "request_delay": 0, "include": "", "exclude": "", "max_pages": 1000,
            "timeout_seconds": 5, "log_level": "INFO",
        }
        worker.start(form)

        for _ in range(50):
            if not worker.is_running:
                break
            time.sleep(0.1)

    state = worker.get_state_snapshot()
    assert state.state == STATE_COMPLETED
    assert state.result_summary is not None
    assert isinstance(state.result_summary, list)


def test_unexpected_exception_during_run_transitions_to_failed(monkeypatch, tmp_path):
    # TestID: EW-006
    monkeypatch.setenv("HOME", str(tmp_path))

    worker = ExecutionWorker()
    worker._orchestrator.run = MagicMock(side_effect=RuntimeError("boom"))

    form = {
        "urls_text": "https://example.com", "mode": "incremental", "word_limit": 450000,
        "request_delay": 0, "include": "", "exclude": "", "max_pages": 1000,
        "timeout_seconds": 5, "log_level": "INFO",
    }
    worker.start(form)

    for _ in range(50):
        if not worker.is_running:
            break
        time.sleep(0.1)

    state = worker.get_state_snapshot()
    assert state.state == STATE_FAILED
    assert "boom" in state.error_message


def test_get_state_snapshot_returns_independent_copy():
    # TestID: EW-007
    worker = ExecutionWorker()

    snapshot1 = worker.get_state_snapshot()
    snapshot1.state = "mutated"
    snapshot1.sites_done = 999

    snapshot2 = worker.get_state_snapshot()

    assert snapshot2.state == STATE_IDLE
    assert snapshot2.sites_done == 0
