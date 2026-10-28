
from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)
import uuid


def generate_id() -> str:
    logger.debug("Generating entity identifier")
    """Generate a unique 32-character hex ID."""
    return uuid.uuid4().hex
