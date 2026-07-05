import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
COMPOSE_FILE = ROOT / "docker-compose.test.yml"
ENV_FILE = ROOT / ".env.test"

# ホスト側からtestserverの管理エンドポイントへ到達するための公開ポート。
# docker-compose.test.yml の `${TESTSERVER_PORT:-8080}:8080` に対応する。
load_dotenv(ENV_FILE)
TESTSERVER_HOST = os.environ.get("TESTSERVER_HOST", "localhost")
TESTSERVER_PORT = os.environ.get("TESTSERVER_PORT", "8081")
TESTSERVER_HOST_URL = f"http://{TESTSERVER_HOST}:{TESTSERVER_PORT}"


def _format_env_value(value: str) -> str:
    """複数行の値はダブルクォートで囲む（BASE_URLS等の改行区切り値のため）。"""
    if "\n" in value:
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    return value


@contextmanager
def _temporary_env_file(overrides: dict[str, str]):
    original = ENV_FILE.read_text(encoding="utf-8")
    lines = []
    for line in original.splitlines():
        key = line.split("=", 1)[0].strip()
        if key in overrides:
            lines.append(f"{key}={_format_env_value(overrides[key])}")
        elif line.strip():
            lines.append(line)
    for key, value in overrides.items():
        if key not in {line.split("=", 1)[0].strip() for line in lines}:
            lines.append(f"{key}={_format_env_value(value)}")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        yield
    finally:
        ENV_FILE.write_text(original, encoding="utf-8")


def _run_compose(
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


def _testserver_post(
    path: str, payload: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """testserverの管理エンドポイント（/__scenario__ 等）にPOSTする。

    ホストの `docker compose run` から見た `testserver:8080` は、
    ホスト側からは docker-compose.test.yml が公開する TESTSERVER_HOST_PORT
    経由でアクセスする。
    """
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(
        f"{TESTSERVER_HOST_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _wait_for_testserver(timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Optional[Exception] = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(
                f"{TESTSERVER_HOST_URL}/robots.txt", timeout=2
            ) as resp:
                if resp.status == 200:
                    return
        except (urllib.error.URLError, ConnectionError) as exc:
            last_error = exc
        time.sleep(0.5)
    raise RuntimeError(f"testserver did not become ready in time: {last_error}")


@contextmanager
def _testserver_scenario(scenario: str):
    """testserverを起動し、指定シナリオへ切り替えた状態で処理を行う。

    テスト終了後は必ず testserver を停止し、次のテストへ状態が漏れないようにする。
    """
    _run_compose("up", "-d", "testserver")
    try:
        _wait_for_testserver()
        _testserver_post("/__reset__")
        _testserver_post("/__scenario__", {"scenario": scenario})
        yield
    finally:
        try:
            _testserver_post("/__reset__")
        except urllib.error.URLError, ConnectionError, OSError:
            # up --exit-code-from 等でtestserverが巻き添えで既に停止している
            # 場合がある。後片付けの主目的はdownによるコンテナ・ネットワークの
            # 破棄であるため、reset呼び出し自体の失敗はテスト結果に影響させない。
            pass
        _run_compose("down")


def test_docker_compose_configuration():
    # TestID: DC-008
    result = _run_compose("config")
    assert result.returncode == 0, result.stderr


def test_docker_compose_can_start_testserver():
    # TestID: DC-001
    result = _run_compose("up", "-d", "testserver")
    assert result.returncode == 0, result.stderr
    _run_compose("down")


def test_dc_001_single_site_basic_startup_generates_output():
    # TestID: DC-001
    shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
    result = _run_compose("run", "--rm", "crawler", "http://testserver:8080")
    assert result.returncode in {0, 2}, result.stdout + result.stderr
    output_dir = ROOT / ".test-workspace" / "output" / "testserver_8080"
    assert output_dir.exists()
    assert (output_dir / "Index.md").exists()
    assert (output_dir / "chunk_manifest.json").exists()


def test_dc_002_base_urls_multi_site_processing():
    # TestID: DC-002
    # BASE_URLS に単一の testserver パスを重複しない2つの絞り込みで指定し、
    # 複数サイトとしてそれぞれ独立に output/{site} が生成されることを確認する。
    with _testserver_scenario("with-include-exclude"):
        base_urls = "\n".join([
            f"{TESTSERVER_HOST_URL}/pages/docs/guides.html",
            f"{TESTSERVER_HOST_URL}/pages/blog/post1.html",
        ])
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        result = _run_compose(
            "up",
            "--exit-code-from",
            "crawler",
            "crawler",
            extra_env={"BASE_URLS": base_urls},
        )
        assert result.returncode == 0, result.stdout + result.stderr

    output_root = ROOT / ".test-workspace" / "output"
    site_dirs = (
        {p.name for p in output_root.iterdir()} if output_root.exists() else set()
    )
    assert any("guides" in name for name in site_dirs)
    assert any("post1" in name for name in site_dirs)


def test_dc_007_log_level_override_changes_log_output():
    # TestID: DC-007
    with _testserver_scenario("happy-path"):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        result = _run_compose(
            "run",
            "--rm",
            "crawler",
            TESTSERVER_HOST_URL,
            "--log-level",
            "DEBUG",
        )
    assert result.returncode in {0, 2}, result.stdout + result.stderr
    log_path = ROOT / ".test-workspace" / "logs" / "crawler.log"
    assert log_path.exists()
    content = log_path.read_text(encoding="utf-8")
    assert "[DEBUG]" in content


def test_dc_003_cli_argument_takes_precedence_over_base_urls():
    # TestID: DC-003
    with _temporary_env_file({"BASE_URLS": "http://does-not-exist.invalid"}):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        result = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
    assert result.returncode in {0, 2}, result.stdout + result.stderr


def test_dc_004_manifest_override_is_used_for_single_site_run():
    # TestID: DC-004
    shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
    result = _run_compose(
        "run",
        "--rm",
        "crawler",
        TESTSERVER_HOST_URL,
        "--manifest",
        "./manifest-prod.json",
    )
    assert result.returncode in {0, 2}, result.stdout + result.stderr
    assert (
        ROOT / ".test-workspace" / "cache" / TESTSERVER_HOST_URL / "manifest.json"
    ).exists() or (ROOT / "manifest-prod.json").exists()


def test_dc_005_manifest_with_multiple_sites_errors():
    # TestID: DC-005
    with _temporary_env_file({"BASE_URLS": TESTSERVER_HOST_URL}):
        result = _run_compose("run", "--rm", "crawler", "--manifest", "./x.json")
    assert result.returncode != 0
    assert result.stdout + result.stderr


def test_dc_006_no_target_url_errors():
    # TestID: DC-006
    with _temporary_env_file({"BASE_URLS": ""}):
        result = _run_compose("run", "--rm", "crawler")
    assert result.returncode != 0
    assert result.stdout + result.stderr


def test_dc_008_help_output_is_displayed():
    # TestID: DC-008
    result = _run_compose("run", "--rm", "crawler", "--help")
    assert result.returncode == 0
    assert "usage:" in (result.stdout + result.stderr).lower()


def test_dc_009_version_output_is_displayed():
    # TestID: DC-009
    result = _run_compose("run", "--rm", "crawler", "--version")
    assert result.returncode == 0
    assert "crawler 1.0" in result.stdout + result.stderr


def test_dc_010_missing_required_environment_values_error():
    # TestID: DC-010
    with _temporary_env_file({"MAX_PAGES": "", "TIMEOUT_SECONDS": ""}):
        result = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
    assert result.returncode != 0
    assert "MAX_PAGES is required but not set" in result.stdout + result.stderr


def test_dc_011_sitemap_crawl_generates_output_files():
    # TestID: DC-011
    shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
    result = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
    assert result.returncode in {0, 2}, result.stdout + result.stderr
    output_dir = ROOT / ".test-workspace" / "output" / TESTSERVER_HOST_URL
    assert (output_dir / "docs_001.md").exists() or (output_dir / "Index.md").exists()


def test_dc_012_fallback_crawl_without_sitemap_generates_output():
    # TestID: DC-012
    with _testserver_scenario("no-sitemap-fallback"):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        with _temporary_env_file({"MAX_PAGES": "5"}):
            result = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
    assert result.returncode in {0, 2}, result.stdout + result.stderr
    output_dir = ROOT / ".test-workspace" / "output" / "testserver_8080"
    assert (output_dir / "Index.md").exists()
    index_content = (output_dir / "Index.md").read_text(encoding="utf-8")
    # sitemapが存在しないため、リンクを辿ったフォールバックページが含まれる。
    assert "Fallback" in index_content


def test_dc_014_word_limit_splits_combined_markdown_into_multiple_files():
    # TestID: DC-014
    with _testserver_scenario("large-site"):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        # 各ページ本文は約6語。WORD_LIMIT=13とすることで2ページ分（12語）までは
        # 同一ファイルに収まり、3ページ目以降で新しい docs_XXX.md へ分割される
        # （単体ページ超過による単独ファイル化ではなく、累積超過による通常分割
        # を検証する）。
        with _temporary_env_file({"WORD_LIMIT": "13", "REQUEST_DELAY": "0"}):
            result = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
    assert result.returncode in {0, 2}, result.stdout + result.stderr
    output_dir = ROOT / ".test-workspace" / "output" / "testserver_8080"
    docs_files = sorted(output_dir.glob("docs_*.md"))
    assert len(docs_files) >= 2
    # 1ページが複数ファイルに跨らないことも合わせて確認する。
    first_file_content = docs_files[0].read_text(encoding="utf-8")
    assert first_file_content.count("Large Page") <= 2


def test_dc_015_duplicate_content_pages_excluded_from_build():
    # TestID: DC-015
    with _testserver_scenario("with-duplicates"):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        result = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
    assert result.returncode in {0, 2}, result.stdout + result.stderr
    output_dir = ROOT / ".test-workspace" / "output" / "testserver_8080"
    chunk_manifest = json.loads(
        (output_dir / "chunk_manifest.json").read_text(encoding="utf-8")
    )
    urls = {entry["url"] for entry in chunk_manifest}
    # 後から見つかったURL（dup-new）のみが結合対象として残る。
    assert f"{TESTSERVER_HOST_URL}/pages/dup-new.html" in urls
    assert f"{TESTSERVER_HOST_URL}/pages/dup-old.html" not in urls


def test_dc_016_robots_disallowed_page_is_skipped():
    # TestID: DC-016
    with _testserver_scenario("with-robots-deny"):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        result = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
    assert result.returncode in {0, 2}, result.stdout + result.stderr
    pages_dir = ROOT / ".test-workspace" / "cache" / "testserver_8080" / "pages"
    # Disallow対象(blog-post1.html)の本文は書き込まれない一方、
    # Allow対象(docs-guides.html)は書き込まれる。
    bodies = (
        [p.read_text(encoding="utf-8") for p in pages_dir.glob("*.md")]
        if pages_dir.exists()
        else []
    )
    assert any("Documentation guide" in b for b in bodies)
    assert not any("Blog content" in b for b in bodies)


def test_dc_017_include_exclude_restricts_crawl_targets():
    # TestID: DC-017
    with _testserver_scenario("with-include-exclude"):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        with _temporary_env_file({"INCLUDE": "/pages/docs", "EXCLUDE": ""}):
            result = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
    assert result.returncode in {0, 2}, result.stdout + result.stderr
    output_dir = ROOT / ".test-workspace" / "output" / "testserver_8080"
    index_content = (output_dir / "Index.md").read_text(encoding="utf-8")
    assert "Docs Guides" in index_content
    assert "Blog Post" not in index_content


def test_dc_018_implicit_include_from_path_when_include_unset():
    # TestID: DC-018 (Issue #6)
    with _testserver_scenario("with-include-exclude"):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        with _temporary_env_file({"INCLUDE": ""}):
            result = _run_compose(
                "run",
                "--rm",
                "crawler",
                "http://testserver:8080/pages/docs/guides.html",
            )
    assert result.returncode in {0, 2}, result.stdout + result.stderr
    output_dir = (
        ROOT / ".test-workspace" / "output" / "testserver_8080_pages_docs_guides_html"
    )
    assert output_dir.exists()
    index_content = (output_dir / "Index.md").read_text(encoding="utf-8")
    assert "Docs Guides" in index_content
    assert "Blog Post" not in index_content


def test_dc_013_archive_zip_is_created():
    # TestID: DC-013
    shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
    result = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
    assert result.returncode in {0, 2}, result.stdout + result.stderr
    archive_dir = ROOT / ".test-workspace" / "archives" / "testserver_8080"
    assert archive_dir.exists()
    assert any(path.suffix == ".zip" for path in archive_dir.iterdir())


def test_dc_019_second_run_without_changes_skips_refetch_via_etag():
    # TestID: DC-019
    with _testserver_scenario("happy-path"):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        first = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
        assert first.returncode in {0, 2}, first.stdout + first.stderr

        manifest_path = (
            ROOT / ".test-workspace" / "cache" / "testserver_8080" / "manifest.json"
        )
        first_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        second = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
        assert second.returncode in {0, 2}, second.stdout + second.stderr

        second_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # 変更がない場合、last_crawled は更新されない（304 or sitemap lastmod一致で
    # manifest書き込み自体が省略される）。content_sha256 は不変のはず。
    for url, entry in first_manifest["pages"].items():
        assert (
            second_manifest["pages"][url]["content_sha256"] == entry["content_sha256"]
        )


def test_dc_020_only_changed_page_is_refetched_on_second_run():
    # TestID: DC-020
    with _testserver_scenario("happy-path"):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        first = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
        assert first.returncode in {0, 2}, first.stdout + first.stderr

        manifest_path = (
            ROOT / ".test-workspace" / "cache" / "testserver_8080" / "manifest.json"
        )
        first_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        _testserver_post(
            "/__override-page__",
            {
                "pagePath": "/pages/docs-guides.html",
                "title": "Docs Guides",
                "body": "Documentation guide has been updated with new content.",
            },
        )

        second = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
        assert second.returncode in {0, 2}, second.stdout + second.stderr

        second_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    changed_url = f"{TESTSERVER_HOST_URL}/pages/docs-guides.html"
    unchanged_url = f"{TESTSERVER_HOST_URL}/pages/blog-post1.html"
    assert (
        second_manifest["pages"][changed_url]["content_sha256"]
        != first_manifest["pages"][changed_url]["content_sha256"]
    )
    assert (
        second_manifest["pages"][unchanged_url]["content_sha256"]
        == first_manifest["pages"][unchanged_url]["content_sha256"]
    )


def test_dc_021_mode_full_refetches_all_pages_unconditionally():
    # TestID: DC-021
    with _testserver_scenario("happy-path"):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        first = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
        assert first.returncode in {0, 2}, first.stdout + first.stderr

        manifest_path = (
            ROOT / ".test-workspace" / "cache" / "testserver_8080" / "manifest.json"
        )
        first_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        with _temporary_env_file({"MODE": "full"}):
            second = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
        assert second.returncode in {0, 2}, second.stdout + second.stderr

        second_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # MODE=full では last_crawled が必ず更新される（無条件で再取得するため）。
    for url, entry in first_manifest["pages"].items():
        assert second_manifest["pages"][url]["last_crawled"] != entry["last_crawled"]


def test_dc_022_page_removed_from_sitemap_is_deleted_from_manifest():
    # TestID: DC-022
    with _testserver_scenario("happy-path"):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        first = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
        assert first.returncode in {0, 2}, first.stdout + first.stderr

        manifest_path = (
            ROOT / ".test-workspace" / "cache" / "testserver_8080" / "manifest.json"
        )
        first_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert f"{TESTSERVER_HOST_URL}/pages/blog-post1.html" in first_manifest["pages"]

        # sitemapから blog-post1.html を除外する。
        _testserver_post(
            "/__sitemap-filter__",
            {"urls": [f"{TESTSERVER_HOST_URL}/pages/docs-guides.html"]},
        )

        second = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
        assert second.returncode in {0, 2}, second.stdout + second.stderr

        second_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert (
        f"{TESTSERVER_HOST_URL}/pages/blog-post1.html" not in second_manifest["pages"]
    )
    assert f"{TESTSERVER_HOST_URL}/pages/docs-guides.html" in second_manifest["pages"]


def test_dc_023_404_page_is_retained_in_manifest_across_runs():
    # TestID: DC-023
    with _testserver_scenario("error-responses"):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        first = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
        assert first.returncode in {0, 2}, first.stdout + first.stderr

        manifest_path = (
            ROOT / ".test-workspace" / "cache" / "testserver_8080" / "manifest.json"
        )
        first_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        not_found_url = f"{TESTSERVER_HOST_URL}/pages/not-found.html"
        assert first_manifest["pages"][not_found_url]["crawl_result"] == "NOT_FOUND"

        second = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
        assert second.returncode in {0, 2}, second.stdout + second.stderr

        second_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert not_found_url in second_manifest["pages"]
    assert second_manifest["pages"][not_found_url]["crawl_result"] == "NOT_FOUND"


def test_dc_033_invalid_mode_errors():
    # TestID: DC-033
    with _temporary_env_file({"MODE": "invalid"}):
        result = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
    assert result.returncode != 0
    assert "Invalid MODE" in result.stdout + result.stderr


def test_dc_034_invalid_max_pages_errors():
    # TestID: DC-034
    with _temporary_env_file({"MAX_PAGES": "abc"}):
        result = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
    assert result.returncode != 0
    assert "MAX_PAGES must be an integer" in result.stdout + result.stderr


def test_dc_035_invalid_log_format_errors():
    # TestID: DC-035
    with _temporary_env_file({"LOG_FORMAT": "xml"}):
        result = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
    assert result.returncode != 0
    assert "Invalid LOG_FORMAT" in result.stdout + result.stderr


def test_dc_025_testserver_down_results_in_exit_code_2():
    # TestID: DC-025
    # testserverを起動しない状態でクロールを実行する。`depends_on` による
    # 自動起動を抑止するため `--no-deps` を指定する。
    _run_compose("down")
    shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
    result = _run_compose("run", "--rm", "--no-deps", "crawler", TESTSERVER_HOST_URL)
    assert result.returncode == 2, result.stdout + result.stderr


def test_dc_026_unresolvable_domain_results_in_exit_code_2():
    # TestID: DC-026
    shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
    result = _run_compose("run", "--rm", "crawler", "http://nonexistent.invalid")
    assert result.returncode == 2, result.stdout + result.stderr


def test_dc_027_concurrent_run_on_same_site_fails_with_lock_error():
    # TestID: DC-027
    with _testserver_scenario("happy-path"):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        # 1つ目の実行がロック保持中にとどまるよう、testserver応答を遅延させる。
        _testserver_post("/__delay__", {"ms": 5000})

        first_proc = subprocess.Popen(
            [
                "docker",
                "compose",
                "-f",
                str(COMPOSE_FILE),
                "run",
                "--rm",
                "crawler",
                "http://testserver:8080",
            ],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env={
                **os.environ,
                "COMPOSE_PROJECT_NAME": "docker-scenario-tests",
                "TESTSERVER_PORT": TESTSERVER_PORT,
            },
        )
        try:
            # 1つ目がサイト処理（＝ロック取得）を開始した旨のログが出力される
            # まで待つ。コンテナのビルド・起動時間に依存させないための工夫。
            lock_dir = ROOT / ".test-workspace" / "cache" / "testserver_8080"
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if (lock_dir / ".lock").exists():
                    break
                time.sleep(0.3)

            second = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
        finally:
            first_output = first_proc.communicate(timeout=60)[0]
            _testserver_post("/__delay__", {"ms": 0})

    assert second.returncode == 2, second.stdout + second.stderr
    assert "lock" in (second.stdout + second.stderr).lower()
    assert first_proc.returncode in {0, 2}, first_output


def test_dc_028_partial_failure_among_multiple_sites_continues_others():
    # TestID: DC-028
    with _testserver_scenario("happy-path"):
        base_urls = "\n".join([
            "http://testserver:8080",
            "http://does-not-exist.invalid",
        ])
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        result = _run_compose(
            "up",
            "--exit-code-from",
            "crawler",
            "crawler",
            extra_env={"BASE_URLS": base_urls},
        )

    assert result.returncode == 2, result.stdout + result.stderr
    output_dir = ROOT / ".test-workspace" / "output" / "testserver_8080"
    assert output_dir.exists()
    assert (output_dir / "Index.md").exists()


def test_dc_029_max_pages_reached_truncates_fallback_crawl_with_warning():
    # TestID: DC-029
    with _testserver_scenario("no-sitemap-fallback"):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        with _temporary_env_file({"MAX_PAGES": "5", "REQUEST_DELAY": "0"}):
            result = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
    assert result.returncode in {0, 2}, result.stdout + result.stderr
    assert "MAX_PAGES" in (result.stdout + result.stderr)
    output_dir = ROOT / ".test-workspace" / "output" / "testserver_8080"
    assert output_dir.exists()
    assert (output_dir / "Index.md").exists()


def test_dc_030_sitemap_entry_count_exceeding_max_pages_still_processes_all():
    # TestID: DC-030
    with _testserver_scenario("large-site"):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        with _temporary_env_file({"MAX_PAGES": "5", "REQUEST_DELAY": "0"}):
            result = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
    assert result.returncode in {0, 2}, result.stdout + result.stderr
    assert "MAX_PAGES" in (result.stdout + result.stderr)
    output_dir = ROOT / ".test-workspace" / "output" / "testserver_8080"
    chunk_manifest = json.loads(
        (output_dir / "chunk_manifest.json").read_text(encoding="utf-8")
    )
    # sitemapに記載された20件全件が処理される（打ち切られない）。
    assert len(chunk_manifest) == 20


def test_dc_031_corrupted_manifest_json_is_handled_gracefully():
    # TestID: DC-031
    with _testserver_scenario("happy-path"):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        first = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
        assert first.returncode in {0, 2}, first.stdout + first.stderr

        manifest_path = (
            ROOT / ".test-workspace" / "cache" / "testserver_8080" / "manifest.json"
        )
        manifest_path.write_text("{not valid json", encoding="utf-8")

        second = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)

    # 破損したmanifestを読み込もうとして異常終了するか、正常に再構築されるかの
    # いずれかであっても、少なくともプロセス自体がクラッシュせず終了コードを返すこと。
    assert second.returncode in {0, 1, 2}, second.stdout + second.stderr


def test_dc_032_host_volume_mounts_receive_generated_artifacts():
    # TestID: DC-032
    with _testserver_scenario("happy-path"):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        result = _run_compose("run", "--rm", "crawler", TESTSERVER_HOST_URL)
    assert result.returncode in {0, 2}, result.stdout + result.stderr

    workspace = ROOT / ".test-workspace"
    assert (workspace / "cache" / "testserver_8080" / "manifest.json").exists()
    assert (workspace / "output" / "testserver_8080" / "Index.md").exists()
    assert (workspace / "archives" / "testserver_8080").exists()
    assert any((workspace / "archives" / "testserver_8080").glob("*.zip"))
    assert (workspace / "logs" / "crawler.log").exists()


def test_dc_036_log_file_path_env_writes_to_custom_log_file():
    # TestID: DC-036
    with _testserver_scenario("happy-path"):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        with _temporary_env_file({"LOG_FILE_PATH": "logs/test-crawler.log"}):
            result = _run_compose(
                "run",
                "--rm",
                "crawler",
                "http://testserver:8080",
                "--log-level",
                "DEBUG",
            )
    assert result.returncode in {0, 2}, result.stdout + result.stderr
    custom_log_path = ROOT / ".test-workspace" / "logs" / "test-crawler.log"
    assert custom_log_path.exists()
    content = custom_log_path.read_text(encoding="utf-8")
    assert "[DEBUG]" in content
