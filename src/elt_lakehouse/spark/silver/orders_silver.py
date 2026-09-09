from pyspark.sql import DataFrame

from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.common.paths import BRONZE_DIR, SILVER_DIR
from src.elt_lakehouse.spark.utils.validations import validation_data

logger = get_logger(__name__)

ORDERS_DELTA_PATH = BRONZE_DIR / "orders_delta"
ORDERS_SILVER_PATH = SILVER_DIR / "orders_silver"


@validation_data(
    delta_path=str(ORDERS_DELTA_PATH),
    schema_name="orders",
    entity="orders",
    output_path=str(ORDERS_SILVER_PATH),
)
def process_orders(df: DataFrame) -> DataFrame:
    """
    Process the orders DataFrame.
    """
    logger.info("Processing orders DataFrame")
    return df


if __name__ == "__main__":
    process_orders()
