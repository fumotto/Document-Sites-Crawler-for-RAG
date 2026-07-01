"""CLIエントリポイント（07_CLI仕様.md）。

使用例:
    docker compose run crawler https://react.dev
    docker compose run crawler https://react.dev --manifest ./manifest-prod.json
    docker compose up
    docker compose run crawler https://react.dev --log-level DEBUG
"""
from __future__ import annotations

import logging
import sys
from typing import List, Optional

from src.app.config.config_loader import load_config
from src.app.exceptions.errors import ConfigError
from src.app.service.orchestrator import EXIT_FATAL
from src.app.service.orchestrator import Orchestrator
from src.app.utils.logging_setup import setup_logging

logger = logging.getLogger(__name__)


def main(argv: Optional[List[str]] = None) -> int:
    # .env を環境変数へロードする（存在しない場合は何もしない）
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    # ConfigError発生時はログ設定が未確定のため、まず最低限のコンソール出力を用意する
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    try:
        config = load_config(argv)
    except ConfigError as exc:
        logger.error(str(exc))
        return EXIT_FATAL

    setup_logging(config.log_level, config.log_format, config.log_file_path)

    logger.info("Starting NotebookLM Document Crawler (mode=%s)", config.mode)

    orchestrator = Orchestrator()
    job_result = orchestrator.run(config)

    for result in job_result.site_results:
        status = "FATAL" if result.has_fatal_error else "OK"
        logger.info(
            "Summary [%s] site=%s pages=%s duplicates_excluded=%s chunks=%s warnings=%s",
            status, result.site_identifier, result.total_pages_included,
            result.duplicate_excluded_count, result.chunk_file_count, len(result.warnings),
        )

    logger.info("Finished with exit code %s", job_result.exit_code)
    return job_result.exit_code


if __name__ == "__main__":
    sys.exit(main())
