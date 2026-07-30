from pyspark.sql import DataFrame
from spark.common.logger import get_logger

logger = get_logger("ingestion.common.writer")


#===============================
# Write DataFrame to Delta Lake
#===============================

# currently using overwrite because we are not using kafka to stream data, so we are not appending data to the delta table.
def write_delta(df : DataFrame, output_path : str , mode : str = "overwrite") -> None:
    """Write a Spark DataFrame to Delta Lake format."""
    try:
        logger.info(
            "Writing DataFrame to Delta Lake: path=%s, mode=%s, columns=%d",
            output_path, 
            mode,
            len(df.columns)
        )

        df.write.format("delta").mode(mode).save(output_path)

        logger.info(
            "DataFrame written to Delta Lake: path=%s, rows=%d",
            output_path,
            df.count(),
        )

    except Exception:
        logger.exception(
            "Failed to write DataFrame to Delta Lake: path=%s, mode=%s", 
            output_path, 
            mode)
        raise