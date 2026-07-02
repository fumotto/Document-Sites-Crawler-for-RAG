"""ExecutionWorker（08_デスクトップアプリ化要件定義書.md 5節）。

バックグラウンドスレッドでOrchestratorを実行し、状態（idle/running/completed/
failed）を管理する。JS側からの `get_status()` ポーリングに応答するための
状態保持のみを責務とし、Orchestrator以降のドメインロジックには一切関与しない
（19節 INT-1: 既存コードとの統合方針）。
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.app.exceptions.errors import ConfigError
from src.app.gui.config_builder import build_config_from_form
from src.app.gui.user_paths import get_app_data_root
from src.app.models.build_result_record import BuildResultRecord
from src.app.service.orchestrator import Orchestrator

logger = logging.getLogger(__name__)

STATE_IDLE = "idle"
STATE_RUNNING = "running"
STATE_COMPLETED = "completed"
STATE_FAILED = "failed"


@dataclass
class ExecutionState:
    state: str = STATE_IDLE
    current_site: Optional[str] = None
    sites_done: int = 0
    sites_total: int = 0
    result_summary: Optional[List[Dict[str, Any]]] = None
    exit_code: Optional[int] = None
    error_message: Optional[str] = None


def _summarize(results: List[BuildResultRecord]) -> List[Dict[str, Any]]:
    return [
        {
            "site_identifier": r.site_identifier,
            "total_pages_included": r.total_pages_included,
            "duplicate_excluded_count": r.duplicate_excluded_count,
            "chunk_file_count": r.chunk_file_count,
            "total_word_count": r.total_word_count,
            "warnings": r.warnings,
            "has_fatal_error": r.has_fatal_error,
            "archive_path": r.archive_path,
        }
        for r in results
    ]


class ExecutionWorker:
    def __init__(self):
        self._lock = threading.Lock()
        self._state = ExecutionState()
        self._thread: Optional[threading.Thread] = None
        self._orchestrator = Orchestrator()

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._state.state == STATE_RUNNING

    def get_state_snapshot(self) -> ExecutionState:
        with self._lock:
            # dataclassの浅いコピーを返す（呼び出し側での不用意な変更を避ける）
            return ExecutionState(**self._state.__dict__)

    def start(self, form_data: Dict[str, Any]) -> None:
        """実行を開始する。既に実行中の場合は何もしない（多重実行防止）。"""
        with self._lock:
            if self._state.state == STATE_RUNNING:
                return

            try:
                config = build_config_from_form(form_data)
            except ConfigError as exc:
                self._state = ExecutionState(state=STATE_FAILED, error_message=str(exc))
                return

            # Issue #4対応: フォームで選択したログレベルは ConfigRecord に格納されるだけでは
            # 反映されない。ルートロガーの実行時レベルをここで明示的に更新する。
            # （CLI版は cli/main.py の setup_logging() 呼び出しで対応済みだが、GUI版は
            # アプリ起動時に一度 setup_logging("INFO", ...) を呼ぶのみで、以降
            # 実行ボタンが押されるたびにログレベルを更新する処理が抜けていた）
            logging.getLogger().setLevel(config.log_level)

            target_count = len(config.base_urls) if config.base_urls else 1
            self._state = ExecutionState(state=STATE_RUNNING, sites_total=target_count, sites_done=0)

        self._thread = threading.Thread(target=self._run, args=(config,), daemon=True)
        self._thread.start()

    def _run(self, config) -> None:
        try:
            root = get_app_data_root()
            job_result = self._orchestrator.run(config, root=root)
            with self._lock:
                self._state.state = STATE_COMPLETED
                self._state.result_summary = _summarize(job_result.site_results)
                self._state.exit_code = job_result.exit_code
                self._state.sites_done = len(job_result.site_results)
        except Exception as exc:  # 予期しない例外もGUIへ確実に伝える（20節）
            logger.exception("Unexpected error during execution")
            with self._lock:
                self._state.state = STATE_FAILED
                self._state.error_message = str(exc)
