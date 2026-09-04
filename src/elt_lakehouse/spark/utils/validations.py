from contracts.schema_utils import field_extract, load_contract
from src.elt_lakehouse.ingestion.core.reader import read_delta
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.common.schema_registry import get_schema_file
from src.elt_lakehouse.spark.quality.schema_validation import check_validation
from src.elt_lakehouse.spark.utils.type_casting import cast_using_contract

logger = get_logger(__name__)


def validation_data(delta_path: str, schema_name: str):
    """
    Summary:
        Validates Delta data against the specified schema contract before
        executing the decorated function.

    Args:
        delta_path (str): Path to the Delta table containing the input data.
        schema_name (str): Name of the schema contract used for validation.

    Returns:
        function: A decorated function that receives the validated DataFrame.
    """

    def decorator(func):
        def wrapper(spark, *args, **kwargs):
            try:
                df = read_delta(spark, delta_path)
                schema_file = get_schema_file(schema_name)
                schema = load_contract(schema_file)
                extract = field_extract(schema)
                type_casted = cast_using_contract(df, extract)
                is_valid, errors = check_validation(type_casted, extract)

                if not is_valid:
                    logger.error("Schema validation failed: %s", errors)
                    raise ValueError(f"Schema validation failed: {errors}")

                logger.info("Schema validation passed: schema=%s", schema_name)

                return func(type_casted, *args, **kwargs)

            except Exception:
                logger.exception("Error during validation: %s", schema_name)
                raise

        return wrapper

    return decorator
