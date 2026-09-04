from pyspark.sql import DataFrame

from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.common.paths import BRONZE_DIR
from src.elt_lakehouse.spark.utils.validations import validation_data

logger = get_logger(__name__)

PAYMENTS_DELTA_PATH = BRONZE_DIR / "payments_delta"


@validation_data(delta_path=str(PAYMENTS_DELTA_PATH), schema_name="payments")
def process_payments(df: DataFrame) -> DataFrame:
    logger.info("Processing payments DataFrame")
    return df


if __name__ == "__main__":
    process_payments()
