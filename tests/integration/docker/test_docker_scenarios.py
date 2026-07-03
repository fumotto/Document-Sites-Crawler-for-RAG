import subprocess
from pathlib import Path


def test_docker_compose_configuration():
    root = Path(__file__).resolve().parent
    result = subprocess.run(
        ["docker", "compose", "-f", "docker-compose.test.yml", "config"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_docker_compose_can_start_testserver():
    root = Path(__file__).resolve().parent
    result = subprocess.run(
        ["docker", "compose", "-f", "docker-compose.test.yml", "up", "-d", "testserver"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    subprocess.run(["docker", "compose", "-f", "docker-compose.test.yml", "down"], cwd=root)
