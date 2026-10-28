
from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)
SCHEMA_REGISTRY = {
    "customers": "customer_schema.json",
    "orders": "order_schema.json",
    "order_items": "order_item_schema.json",
    "products": "products_schema.json",
    "payments": "payment_schema.json",
    "reviews": "review_schema.json",
    "geolocation": "geolocation_schema.json",
    "sellers": "seller_schema.json",
}


def get_schema_file(schema_name: str):
    try:
        return SCHEMA_REGISTRY[schema_name]
    except KeyError:
        logger.exception("operation failed; re-raising")
        raise ValueError(f"Schema '{schema_name}' not found in the schema registry.")
