import subprocess
from pathlib import Path


def test_playwright_integration_runner():
    root = Path(__file__).resolve().parent
    result = subprocess.run(
        ['npx', 'playwright', 'test', '--config', 'playwright.config.ts'],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
