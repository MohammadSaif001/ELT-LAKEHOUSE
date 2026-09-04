from src.elt_lakehouse.ingestion.core.reader import read_json
from src.elt_lakehouse.ingestion.core.writer import write_delta
from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)


def ingestor(input_path: str, output_path: str, spark, mode: str = "overwrite"):
    try:
        logger.info(
            "Starting ingestion: input_path=%s, output_path=%s",
            input_path,
            output_path,
        )
        df = read_json(spark, input_path)
        write_delta(df=df, output_path=output_path, mode=mode)
        logger.info(
            "Ingestion completed successfully: output_path=%s",
            output_path,
        )
    except Exception:
        logger.exception(
            "Error occurred while ingesting data: input_path=%s, output_path=%s",
            input_path,
            output_path,
        )
        raise
