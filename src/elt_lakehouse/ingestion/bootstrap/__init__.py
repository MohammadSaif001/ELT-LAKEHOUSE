"""Bootstrap ingestion package."""

from elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)
logger.debug("Bootstrap ingestion package loaded")
