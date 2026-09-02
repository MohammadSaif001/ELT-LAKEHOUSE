from pyspark.sql import DataFrame
from src.elt_lakehouse.spark.common.paths import BRONZE_DIR
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.utils.validations import validation_data

logger = get_logger(__name__)

PRODUCTS_DELTA_PATH = BRONZE_DIR / "products_delta"


@validation_data(
    delta_path=str(PRODUCTS_DELTA_PATH),
    schema_name="products"
)
def process_products(df: DataFrame) -> DataFrame:
    logger.info("Processing products DataFrame")
    return df


if __name__ == "__main__":
    process_products()
