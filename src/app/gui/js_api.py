"""JSに公開するAPIクラス（08_デスクトップアプリ化要件定義書.md 5, 20節）。

PyWebViewの js_api 機構により、このクラスのpublicメソッドがJS側から
`pywebview.api.<method_name>(...)` として呼び出せるようになる。
"""
from __future__ import annotations

import logging
import subprocess
import sys
from typing import Any, Dict

from src.app.gui.explorer_handler import Explorer_handler
from src.app.gui.execution_worker import ExecutionWorker
from src.app.gui.log_buffer import InMemoryLogHandler
from src.app.gui.settings_store import load_settings, save_settings
from src.app.gui.user_paths import get_log_file_path

logger = logging.getLogger(__name__)


class JsApi:
    def __init__(self, log_handler: InMemoryLogHandler):
        self._worker = ExecutionWorker()
        self._log_handler = log_handler
        self.explorer_handler = Explorer_handler()

    # --- 4.3節: 設定値の永続化 ---------------------------------------------

    def load_settings(self) -> Dict[str, Any]:
        return load_settings()

    # --- 5節: 実行の開始 ------------------------------------------------

    def start_execution(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        if self._worker.is_running:
            return {"status": "already_running"}

        # 実行開始時点の入力値を保存する（IMPL-4）
        try:
            save_settings(form_data)
        except Exception:
            logger.warning("Failed to save settings.json", exc_info=True)

        self._worker.start(form_data)
        return {"status": "started"}

    # --- 5.4節: ポーリングによる状態取得 -------------------------------------

    def get_status(self, since_index: int = -1) -> Dict[str, Any]:
        state = self._worker.get_state_snapshot()
        log_entries = self._log_handler.get_lines_since(since_index)

        return {
            "state": state.state,
            "log_lines": [e.text for e in log_entries],
            "last_index": log_entries[-1].index if log_entries else since_index,
            "current_site": state.current_site,
            "sites_done": state.sites_done,
            "sites_total": state.sites_total,
            "result_summary": state.result_summary,
            "exit_code": state.exit_code,
            "error_message": state.error_message,
        }

    # --- 20節: エラー時のログファイルを開く ---------------------------------

    def open_log_folder(self) -> Dict[str, Any]:
        log_path = get_log_file_path()
        try:
            if sys.platform == "win32":
                subprocess.run(["explorer", "/select,", str(log_path)], check=False)
            elif sys.platform == "darwin":
                subprocess.run(["open", "-R", str(log_path)], check=False)
            else:
                subprocess.run(["xdg-open", str(log_path.parent)], check=False)
            return {"status": "opened"}
        except Exception as exc:
            logger.warning("Failed to open log folder", exc_info=True)
            return {"status": "error", "message": str(exc)}

    def open_output_directory(self):
        self.explorer_handler.open_output_directory(None)

    # --- アプリバージョン情報 ---------------------------------------------

    def get_app_info(self) -> Dict[str, Any]:
        from src.app.gui import app_version

        return {
            "app_name": app_version.APP_NAME,
            "version": app_version.APP_VERSION,
        }
