from pathlib import Path
import os
import subprocess
from typing import Dict, Optional

ROOT = Path(__file__).resolve().parent.parent
COMPOSE_FILE = ROOT / "docker-compose.test.yml"
ENV_FILE = ROOT / ".env.test"


def run_docker_compose(
    *args: str,
    extra_env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess[str]:
    """docker compose を実行する。

    extra_env を渡した場合、docker-compose.test.yml の `environment:` セクションが
    参照する `TEST_OVERRIDE_*` 変数として、compose プロセス自身の環境変数を通じて
    値を渡す（`.env` ファイル方式は改行を含む値の扱いが不確実なため使用しない）。
    現状 `BASE_URLS` のみサポートする（`TEST_OVERRIDE_BASE_URLS`）。
    """
    env = {
        **os.environ,
        "COMPOSE_PROJECT_NAME": "docker-scenario-tests",
        "TESTSERVER_PORT": os.environ.get("TESTSERVER_PORT", "8080"),
    }

    # マウント先をDocker任せで自動作成させるとroot所有になりうるため、
    # ホスト側で先に作成しておく。crawlerコンテナ自体はrootで動作するため、
    # 生成物はroot所有になる。テスト側での読み取りには影響しない
    # （root権限で読める）が、次回pytest実行前のクリーンアップ（rmtree等）で
    # PermissionErrorになりうるため、後片付け時にsudoが必要になる場合がある。
    for subdir in ("cache", "output", "archives", "logs"):
        (ROOT / ".test-workspace" / subdir).mkdir(parents=True, exist_ok=True)

    if extra_env:
        for key, value in extra_env.items():
            env[f"TEST_OVERRIDE_{key}"] = value

    result = subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    return result
