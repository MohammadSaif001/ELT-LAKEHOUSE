from pyspark.sql import DataFrame

from src.elt_lakehouse.spark.common.logger import get_logger, kv

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


def check_and_deduplicate(df: DataFrame, entity: str) -> DataFrame:
    """Deduplicate a DataFrame using the entity's configured key columns.

    Uses ``dropDuplicates`` directly — no shuffle aggregation. If the entity
    has no configured key columns, deduplication is skipped and the original
    DataFrame is returned unchanged.

    Args:
        df: Input DataFrame to deduplicate.
        entity: Entity name used to look up the deduplication key columns.

    Returns:
        Deduplicated DataFrame (or the original if no key columns are defined).
    """
    key_columns = DUPLICATE_KEY_COLUMNS.get(entity)

    if key_columns is None:
        logger.warning(
            "%s_deduplication_skipped %s",
            entity,
            kv(reason="No key columns defined for deduplication"),
        )
        return df

    deduped = df.dropDuplicates(key_columns)
    logger.info(
        "%s_deduplication_applied %s",
        entity,
        kv(keys=",".join(key_columns)),
    )
    return deduped
