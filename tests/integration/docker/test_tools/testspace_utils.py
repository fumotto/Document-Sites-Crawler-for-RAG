import shutil
from pathlib import Path

from .docker_executer import run_docker_compose

TEST_ROOT = Path(__file__).resolve().parent.parent
TEST_WORKSPACE = TEST_ROOT / ".test-workspace"


def clean_test_workspace() -> None:
    """.test-workspace 配下を完全にクリーンな状態にする。

    crawlerコンテナ（root）が生成したファイル・ディレクトリは、ホスト側の
    非rootユーザーからは削除権限が無い場合がある。shutil.rmtree(..., ignore_errors=True)
    はこの失敗を握りつぶし、古いテストの残骸（別シナリオでのmanifest.json等）が
    削除されないまま次のテストへ混入する原因になっていた。
    ホスト側での削除を試みたあと、crawlerコンテナ自身（root）にも削除させることで
    確実にクリーンな状態を保証する。
    """
    workspace = TEST_WORKSPACE
    shutil.rmtree(workspace, ignore_errors=True)
    if workspace.exists():
        run_docker_compose(
            "run",
            "--rm",
            "--no-deps",
            "--entrypoint",
            "sh",
            "crawler",
            "-c",
            "rm -rf /app/cache/* /app/output/* /app/archives/* /app/logs/*",
        )
        shutil.rmtree(workspace, ignore_errors=True)
    for subdir in ("cache", "output", "archives", "logs"):
        (workspace / subdir).mkdir(parents=True, exist_ok=True)
