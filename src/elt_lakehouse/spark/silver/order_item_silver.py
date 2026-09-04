from pyspark.sql import DataFrame

from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.common.paths import BRONZE_DIR
from src.elt_lakehouse.spark.utils.validations import validation_data

logger = get_logger(__name__)

ORDER_ITEMS_DELTA_PATH = BRONZE_DIR / "order_items_delta"


@validation_data(delta_path=str(ORDER_ITEMS_DELTA_PATH), schema_name="order_items")
def process_order_items(df: DataFrame) -> DataFrame:
    logger.info("Processing order items DataFrame")
    return df


if __name__ == "__main__":
    process_order_items()
