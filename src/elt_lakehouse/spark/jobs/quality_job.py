"""Spark data-quality job entry point."""

from elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)
logger.debug("Quality job module loaded")
