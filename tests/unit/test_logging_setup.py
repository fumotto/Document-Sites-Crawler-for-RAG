import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import os

from src.app.utils.logging_setup import setup_logging


def assert_readable_and_writable(path: Path) -> None:
    assert os.access(path, os.R_OK)
    assert os.access(path, os.W_OK)


def test_setup_logging_creates_readable_file(tmp_path: Path) -> None:
    # TestID: LOG-001
    log_path = tmp_path / "crawler.log"

    setup_logging("INFO", "text", log_path)

    assert_readable_and_writable(log_path)


def test_log_level_applied_to_root_logger(tmp_path: Path) -> None:
    # TestID: LOG-002
    log_path = tmp_path / "crawler.log"

    setup_logging("ERROR", "text", log_path)

    assert logging.getLogger().level == logging.ERROR


def test_text_format_output(tmp_path: Path) -> None:
    # TestID: LOG-003
    log_path = tmp_path / "crawler.log"
    setup_logging("INFO", "text", log_path)

    logger = logging.getLogger("test_text_format")
    logger.info("hello text format")
    for handler in logging.getLogger().handlers:
        handler.flush()

    content = log_path.read_text(encoding="utf-8")
    assert "hello text format" in content
    assert "[INFO]" in content


def test_json_format_output_is_parseable(tmp_path: Path) -> None:
    # TestID: LOG-004
    log_path = tmp_path / "crawler.log"
    setup_logging("INFO", "json", log_path)

    logger = logging.getLogger("test_json_format")
    logger.info("hello json format")
    for handler in logging.getLogger().handlers:
        handler.flush()

    lines = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines
    parsed = json.loads(lines[-1])
    assert parsed["message"] == "hello json format"
    assert parsed["level"] == "INFO"


def test_repeated_setup_does_not_accumulate_handlers(tmp_path: Path) -> None:
    # TestID: LOG-005
    log_path = tmp_path / "crawler.log"

    setup_logging("INFO", "text", log_path)
    first_count = len(logging.getLogger().handlers)

    setup_logging("INFO", "text", log_path)
    second_count = len(logging.getLogger().handlers)

    assert first_count == second_count


def test_rotating_file_handler_parameters(tmp_path: Path) -> None:
    # TestID: LOG-006
    log_path = tmp_path / "crawler.log"

    setup_logging("INFO", "text", log_path)

    rotating_handlers = [
        h for h in logging.getLogger().handlers if isinstance(h, RotatingFileHandler)
    ]
    assert len(rotating_handlers) == 1
    handler = rotating_handlers[0]
    assert handler.maxBytes == 10 * 1024 * 1024
    assert handler.backupCount == 5
