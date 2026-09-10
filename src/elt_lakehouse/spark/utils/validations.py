from functools import wraps

from pyspark.storagelevel import StorageLevel

from contracts.schema_utils import field_extract, load_contract
from src.elt_lakehouse.ingestion.core.reader import read_delta
from src.elt_lakehouse.ingestion.core.writer import write_delta
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.common.schema_registry import get_schema_file
from src.elt_lakehouse.spark.quality.duplicate_checks import check_and_deduplicate
from src.elt_lakehouse.spark.quality.null_checks import check_nulls
from src.elt_lakehouse.spark.quality.schema_validation import check_validation
from src.elt_lakehouse.spark.utils.type_casting import cast_using_contract

logger = get_logger(__name__)


def validation_data(delta_path: str, schema_name: str, entity: str, output_path: str):
    """Validate a Delta table before calling the decorated transformation.

    The decorator loads the configured contract, casts the input columns,
    removes rows that violate non-nullable fields, writes those rows to the
    {output_path}/quarantine path, and deduplicates the remaining rows using
    the entity's configured key columns. Geolocation data is exempt from
    deduplication. The decorated function receives the resulting Spark
    DataFrame as its first argument.

    Args:
        delta_path: Path to the input Delta table.
        schema_name: Name of the schema contract to load.
        entity: Entity name used to select duplicate key columns.
        output_path: Base path used for the quarantine data written by the
            decorator.

    Returns:
        A decorator for a function whose first argument is a Spark DataFrame.

    Raises:
        ValueError: If the cleaned and deduplicated data fails schema
            validation.
        Exception: Any read, cast, quality-check, or write error is logged and
            re-raised.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(spark, *args, **kwargs):
            try:
                df = read_delta(spark, delta_path)

                schema_file = get_schema_file(schema_name)

                schema = load_contract(schema_file)

                extract = field_extract(schema)

                type_casted = cast_using_contract(df, extract).persist(
                    StorageLevel.MEMORY_AND_DISK
                )

                clean_df, quarantine_df = check_nulls(type_casted, extract)
                quarantine_df = quarantine_df.persist(StorageLevel.MEMORY_AND_DISK)

                if quarantine_df.limit(1).count() > 0:
                    logger.warning(
                        "Quarantine data is not empty: entity=%s, output_path=%s",
                        entity,
                        output_path
                    )
                    write_delta(
                        quarantine_df,
                        output_path=f"{output_path}/quarantine",
                        mode="overwrite",
                    )
                quarantine_df.unpersist()
                type_casted.unpersist()

                if entity == "geolocation":
                    no_duplicate_df = clean_df
                    logger.info("Skipping duplicate check for geolocation data.")
                    """
                        Geolocation data is skipped from duplicate checks because
                        it is assumed that the geolocation data may contain
                        multiple entries for the same location with different
                        attributes. Therefore, we do not perform duplicate checks
                        on geolocation data to avoid losing potentially valuable
                        information. This decision is based on the specific nature
                        of geolocation data and the requirements of the application.
                    """
                else:
                    no_duplicate_df = check_and_deduplicate(clean_df, entity=entity)
                no_duplicate_df = no_duplicate_df.persist(StorageLevel.MEMORY_AND_DISK)
                is_valid, errors = check_validation(no_duplicate_df, extract)

                if not is_valid:
                    logger.error("Schema validation failed: %s", errors)
                    no_duplicate_df.unpersist()
                    raise ValueError(f"Schema validation failed: {errors}")

                logger.info("Schema validation passed: schema=%s", schema_name)

                no_duplicate_df = no_duplicate_df.cache()

                return func(no_duplicate_df, *args, **kwargs)

            except Exception:
                logger.exception("Error during validation: %s", schema_name)
                raise

        return wrapper

    return decorator
