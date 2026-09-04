from pyspark.sql import DataFrame

from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.common.paths import BRONZE_DIR
from src.elt_lakehouse.spark.utils.validations import validation_data

logger = get_logger(__name__)

GEOLOCATION_DELTA_PATH = BRONZE_DIR / "geolocation_delta"


@validation_data(delta_path=str(GEOLOCATION_DELTA_PATH), schema_name="geolocation")
def process_geolocation(df: DataFrame) -> DataFrame:
    logger.info("Processing geolocation DataFrame")
    return df


if __name__ == "__main__":
    process_geolocation()
