from pyspark.sql import DataFrame
from src.elt_lakehouse.spark.common.paths import BRONZE_DIR
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.utils.validations import validation_data

logger = get_logger(__name__)

CUSTOMERS_DELTA_PATH = BRONZE_DIR / "customers_delta"


@validation_data(
    delta_path=str(CUSTOMERS_DELTA_PATH),
    schema_name="customers"
)
def process_customers(df: DataFrame) -> DataFrame:
    logger.info("Processing customers DataFrame")
    return df


if __name__ == "__main__":
    process_customers()
