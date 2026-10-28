"""Warehouse loader package."""
from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)
logger.debug("Warehouse loaders package loaded")