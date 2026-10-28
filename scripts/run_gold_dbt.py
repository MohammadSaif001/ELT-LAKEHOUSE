"""Compatibility entry point for the Gold dbt job."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.jobs.gold_job import main  # noqa: E402

logger = get_logger(__name__)


if __name__ == "__main__":
    logger.info("Starting Gold dbt compatibility entry point")
    main()
    logger.info("Gold dbt compatibility entry point completed")
