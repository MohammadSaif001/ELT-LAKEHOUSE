from pyspark.sql import DataFrame

from src.elt_lakehouse.spark.common.logger import get_logger, kv, log_duration

logger = get_logger(__name__)

DUPLICATE_KEY_COLUMNS: dict[str, list[str]] = {
    "customers": ["customer_id"],
    "orders": ["order_id"],
    "products": ["product_id"],
    "order_items": ["order_id", "order_item_id"],
    "payments": ["order_id", "payment_sequential"],
    "reviews": ["review_id"],
    "sellers": ["seller_id"],
}


def check_duplicates(
    df: DataFrame, entity: str, key_columns: list[str]
) -> tuple[bool, int]:

    with log_duration(logger, f"{entity}_duplicate_check", keys=",".join(key_columns)):
        duplicate_count = df.groupBy(key_columns).count().filter("count > 1").count()

    is_clean = duplicate_count == 0

    if is_clean:
        logger.info("%s_duplicates %s", entity, kv(found=0))
    else:
        logger.warning(
            "%s_duplicates %s",
            entity,
            kv(found=duplicate_count, keys=",".join(key_columns)),
        )
    return is_clean, duplicate_count


def check_and_deduplicate(df: DataFrame, entity: str) -> DataFrame:
    key_columns = DUPLICATE_KEY_COLUMNS.get(entity)

    if key_columns is None:
        logger.warning(
            "%s_deduplication_skipped %s",
            entity,
            kv(reason="No key columns defined for deduplication"),
        )
        return df

    is_clean, duplicate_count = check_duplicates(df, entity, key_columns)

    if not is_clean:
        df = df.dropDuplicates(key_columns)

        logger.warning(
            "%s_deduplicated %s",
            entity,
            kv(
                duplicate_groups=duplicate_count,
                keys=",".join(key_columns),
            ),
        )

    return df
