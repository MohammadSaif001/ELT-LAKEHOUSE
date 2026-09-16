from pathlib import Path

from src.elt_lakehouse.ingestion.core.reader import read_json, read_parquet
from src.elt_lakehouse.ingestion.core.writer import write_delta
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.utils.memory import monitor_memory

logger = get_logger(__name__)


@monitor_memory
def ingestor(input_path: str, output_path: str, spark, mode: str = "overwrite"):
    try:
        logger.info(
            "Starting ingestion: input_path=%s, output_path=%s",
            input_path,
            output_path,
        )
        path_obj = Path(input_path)
        parquet_alt = path_obj.with_suffix(".parquet")
        if path_obj.suffix == ".parquet" or (
            not path_obj.exists() and parquet_alt.exists()
        ):
            actual_input = str(
                path_obj if path_obj.suffix == ".parquet" else parquet_alt
            )
            df = read_parquet(spark, actual_input)
        else:
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
