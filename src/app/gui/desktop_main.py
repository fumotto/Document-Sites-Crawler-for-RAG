"""GUIエントリポイント（08_デスクトップアプリ化要件定義書.md 3, 5, 7節）。

PyWebViewでウィンドウを起動し、`web/index.html` を表示する。
起動時にMutexでアプリの多重起動を防止する（7節）。

注意: 本モジュールはPyWebView（および、Windows環境でのみ多重起動防止に
使用するpywin32）に依存する。開発環境にこれらがインストールされていない
場合でも import エラーで落ちないよう、フォールバックを用意している。
実際の起動確認は、要件定義書08節に基づく実機（Windows + PyInstallerビルド）
でのテストが別途必要である。
"""
from __future__ import annotations

import logging
import sys

from src.app.gui import app_version
from src.app.gui.js_api import JsApi
from src.app.gui.log_buffer import InMemoryLogHandler
from src.app.gui.user_paths import get_log_file_path
from src.app.utils.logging_setup import setup_logging

logger = logging.getLogger(__name__)

MUTEX_NAME = "Global\\DocumentSitesCrawlerForRAG_SingleInstanceMutex"


def _acquire_single_instance_lock():
    """7節: アプリ単位の多重起動防止。Windows名前付きMutexを使用する（IMPL-5）。

    Returns:
        取得したMutexハンドル（解放不要、プロセス終了時にOSが自動解放する）。
        取得に失敗した場合（既に起動中）は None を返す。
        Windows以外の環境ではチェックをスキップし、常に取得成功として扱う。
    """
    if sys.platform != "win32":
        logger.info("Single-instance check is skipped on non-Windows platform (dev environment).")
        return object()  # 常にTruthyなダミー値

    try:
        import win32api
        import win32event
        import winerror

        mutex = win32event.CreateMutex(None, False, MUTEX_NAME)
        last_error = win32api.GetLastError()
        if last_error == winerror.ERROR_ALREADY_EXISTS:
            return None
        return mutex
    except ImportError:
        logger.warning("pywin32 is not installed; single-instance check is skipped.")
        return object()


def _setup_logging_and_buffer() -> InMemoryLogHandler:
    setup_logging(log_level="INFO", log_format="text", log_file_path=get_log_file_path())
    handler = InMemoryLogHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logging.getLogger().addHandler(handler)
    return handler


def main() -> int:
    lock = _acquire_single_instance_lock()
    if lock is None:
        # 既に起動中。将来的には既存ウィンドウのアクティブ化を行いたいが、
        # 初期リリースでは単純にメッセージを出して終了する（7節）。
        print(f"{app_version.APP_NAME} は既に起動しています。")
        return 1

    log_handler = _setup_logging_and_buffer()
    logger.info("Starting %s v%s", app_version.APP_NAME, app_version.APP_VERSION)

    try:
        import webview
    except ImportError:
        logger.error(
            "pywebview is not installed. Install requirements-desktop.txt to run the GUI."
        )
        return 1

    js_api = JsApi(log_handler)

    window = webview.create_window(
        title=app_version.APP_NAME,
        url="web/index.html",
        js_api=js_api,
        width=900,
        height=700,
        min_size=(700, 500),
    )

    def on_closing() -> bool:
        """IMPL-2: 実行中にウィンドウを閉じようとした場合は確認ダイアログを出す。"""
        if not js_api._worker.is_running:  # noqa: SLF001 - GUI層内部での直接参照
            return True
        try:
            return window.evaluate_js("alert('処理中は閉じれません');")
        except Exception:
            logger.warning("Failed to show close-confirmation dialog; allowing close.", exc_info=True)
            return True

    window.events.closing += on_closing

    webview.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
