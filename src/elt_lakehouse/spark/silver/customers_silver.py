from pyspark.sql import DataFrame

from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.common.paths import BRONZE_DIR, SILVER_DIR
from src.elt_lakehouse.spark.utils.validations import validation_data

logger = get_logger(__name__)

CUSTOMERS_DELTA_PATH = BRONZE_DIR / "customers_delta"
CUSTOMERS_SILVER_PATH = SILVER_DIR / "customers_silver"


@validation_data(
    delta_path=str(CUSTOMERS_DELTA_PATH),
    schema_name="customers",
    entity="customers",
    output_path=str(CUSTOMERS_SILVER_PATH),
)
def process_customers(df: DataFrame) -> DataFrame:
    logger.info("Processing customers DataFrame")

    return df


if __name__ == "__main__":
    process_customers()
