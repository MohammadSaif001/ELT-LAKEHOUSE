from pyspark.sql import DataFrame

from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.common.paths import BRONZE_DIR
from src.elt_lakehouse.spark.utils.validations import validation_data

logger = get_logger(__name__)

REVIEWS_DELTA_PATH = BRONZE_DIR / "reviews_delta"


@validation_data(delta_path=str(REVIEWS_DELTA_PATH), schema_name="reviews")
def process_reviews(df: DataFrame) -> DataFrame:
    logger.info("Processing reviews DataFrame")
    return df


if __name__ == "__main__":
    process_reviews()
