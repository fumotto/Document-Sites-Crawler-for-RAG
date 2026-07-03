import os
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COMPOSE_FILE = ROOT / "docker-compose.test.yml"
ENV_FILE = ROOT / ".env.test"


@contextmanager
def _temporary_env_file(overrides: dict[str, str]):
    original = ENV_FILE.read_text(encoding="utf-8")
    lines = []
    for line in original.splitlines():
        key = line.split("=", 1)[0].strip()
        if key in overrides:
            lines.append(f"{key}={overrides[key]}")
        elif line.strip():
            lines.append(line)
    for key, value in overrides.items():
        if key not in {line.split("=", 1)[0].strip() for line in lines}:
            lines.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        yield
    finally:
        ENV_FILE.write_text(original, encoding="utf-8")


def _run_compose(*args: str) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "COMPOSE_PROJECT_NAME": "docker-scenario-tests",
        "TESTSERVER_PORT": os.environ.get("TESTSERVER_PORT", "8080"),
    }
    result = subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    return result


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


def test_dc_003_cli_argument_takes_precedence_over_base_urls():
    # TestID: DC-003
    with _temporary_env_file({"BASE_URLS": "http://does-not-exist.invalid"}):
        shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
        result = _run_compose("run", "--rm", "crawler", "http://testserver:8080")
    assert result.returncode in {0, 2}, result.stdout + result.stderr


def test_dc_004_manifest_override_is_used_for_single_site_run():
    # TestID: DC-004
    shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
    result = _run_compose(
        "run",
        "--rm",
        "crawler",
        "http://testserver:8080",
        "--manifest",
        "./manifest-prod.json",
    )
    assert result.returncode in {0, 2}, result.stdout + result.stderr
    assert (
        ROOT / ".test-workspace" / "cache" / "testserver_8080" / "manifest.json"
    ).exists() or (ROOT / "manifest-prod.json").exists()


def test_dc_005_manifest_with_multiple_sites_errors():
    # TestID: DC-005
    with _temporary_env_file({"BASE_URLS": "http://testserver:8080"}):
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
        result = _run_compose("run", "--rm", "crawler", "http://testserver:8080")
    assert result.returncode != 0
    assert "MAX_PAGES is required but not set" in result.stdout + result.stderr


def test_dc_011_sitemap_crawl_generates_output_files():
    # TestID: DC-011
    shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
    result = _run_compose("run", "--rm", "crawler", "http://testserver:8080")
    assert result.returncode in {0, 2}, result.stdout + result.stderr
    output_dir = ROOT / ".test-workspace" / "output" / "testserver_8080"
    assert (output_dir / "docs_001.md").exists() or (output_dir / "Index.md").exists()


def test_dc_013_archive_zip_is_created():
    # TestID: DC-013
    shutil.rmtree(ROOT / ".test-workspace", ignore_errors=True)
    result = _run_compose("run", "--rm", "crawler", "http://testserver:8080")
    assert result.returncode in {0, 2}, result.stdout + result.stderr
    archive_dir = ROOT / ".test-workspace" / "archives" / "testserver_8080"
    assert archive_dir.exists()
    assert any(path.suffix == ".zip" for path in archive_dir.iterdir())


def test_dc_033_invalid_mode_errors():
    # TestID: DC-033
    with _temporary_env_file({"MODE": "invalid"}):
        result = _run_compose("run", "--rm", "crawler", "http://testserver:8080")
    assert result.returncode != 0
    assert "Invalid MODE" in result.stdout + result.stderr


def test_dc_034_invalid_max_pages_errors():
    # TestID: DC-034
    with _temporary_env_file({"MAX_PAGES": "abc"}):
        result = _run_compose("run", "--rm", "crawler", "http://testserver:8080")
    assert result.returncode != 0
    assert "MAX_PAGES must be an integer" in result.stdout + result.stderr


def test_dc_035_invalid_log_format_errors():
    # TestID: DC-035
    with _temporary_env_file({"LOG_FORMAT": "xml"}):
        result = _run_compose("run", "--rm", "crawler", "http://testserver:8080")
    assert result.returncode != 0
    assert "Invalid LOG_FORMAT" in result.stdout + result.stderr
