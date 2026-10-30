"""Incremental Spark processing package."""

from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)
logger.debug("Incremental Spark package loaded")
