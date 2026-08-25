from pyspark.sql import DataFrame
from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)


# ===============================
# Write DataFrame to Delta Lake
# ===============================


# currently using overwrite because we are not using kafka to stream data, so we are not appending data to the delta table.
def write_delta(
    df: DataFrame, output_path: str, mode: str = "overwrite"
) -> None:
    """Write a Spark DataFrame to Delta Lake format."""
    try:
        DATAFRAME_LENGTH = len(df.columns)
        logger.info(
            "Writing DataFrame to Delta Lake: path=%s, mode=%s, columns=%d",
            output_path,
            mode,
            DATAFRAME_LENGTH,
        )

        df.write.format("delta").mode(mode).save(output_path)

        logger.info(
            "DataFrame written to Delta Lake: path=%s, columns=%d",
            output_path,
            DATAFRAME_LENGTH,
        )

    except Exception:
        logger.exception(
            "Failed to write DataFrame to Delta Lake: path=%s, mode=%s",
            output_path,
            mode,
        )
        raise
