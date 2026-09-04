from pyspark.sql import DataFrame

from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.common.paths import BRONZE_DIR
from src.elt_lakehouse.spark.utils.validations import validation_data

logger = get_logger(__name__)

SELLERS_DELTA_PATH = BRONZE_DIR / "sellers_delta"


@validation_data(delta_path=str(SELLERS_DELTA_PATH), schema_name="sellers")
def process_sellers(df: DataFrame) -> DataFrame:
    logger.info("Processing sellers DataFrame")
    return df


if __name__ == "__main__":
    process_sellers()
