from pyspark.sql import SparkSession, DataFrame
from delta import configure_spark_with_delta_pip

from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)


def get_spark() -> SparkSession:
    builder = (
        SparkSession.builder.appName("ELT-Lakehouse")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
    )

    return configure_spark_with_delta_pip(builder).getOrCreate()


def read_customers_delta() -> DataFrame:
    """
    Reads the customers Delta table from the bronze layer.
    """
    try:
        spark = get_spark()

        df: DataFrame = spark.read.format("delta").load(
            "storage/bronze/customers_delta"
        )

        logger.info("Successfully loaded customers Delta table")

        return df

    except Exception as e:
        logger.error(f"Error reading Delta table: {e}")
        raise


if __name__ == "__main__":
    df = read_customers_delta()
    df.show()
