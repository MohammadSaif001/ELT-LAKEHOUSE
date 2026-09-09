from pyspark.sql import DataFrame

from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.common.paths import BRONZE_DIR, SILVER_DIR
from src.elt_lakehouse.spark.utils.validations import validation_data

logger = get_logger(__name__)

REVIEWS_DELTA_PATH = BRONZE_DIR / "reviews_delta"
REVIEWS_SILVER_PATH = SILVER_DIR / "reviews_silver"


@validation_data(
    delta_path=str(REVIEWS_DELTA_PATH),
    schema_name="reviews",
    entity="reviews",
    output_path=str(REVIEWS_SILVER_PATH),
)
def process_reviews(df: DataFrame) -> DataFrame:
    logger.info("Processing reviews DataFrame")
    return df


if __name__ == "__main__":
    process_reviews()
