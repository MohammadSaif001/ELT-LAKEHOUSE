"""Change-data-capture handling helpers."""
from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)
logger.debug("CDC handler module loaded")