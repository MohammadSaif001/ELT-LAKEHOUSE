"""Postgres serving writer integration."""
from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)
logger.debug("Postgres writer module loaded")