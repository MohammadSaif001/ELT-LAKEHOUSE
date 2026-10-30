"""Names and log evidence for stages wired into the ELT orchestration."""

from __future__ import annotations

from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Job:
    key: str
    label: str
    # Substrings expected in log messages for this job, used to match
    # log lines back to a specific job (see log_reader.py).
    log_match: str
    # Optional output path (relative to project root), reported separately
    # from execution status.
    artifact_path: str | None = None


@dataclass(frozen=True)
class Stage:
    key: str
    label: str
    logger_name: str
    completion_match: str
    jobs: list[Job] = field(default_factory=list)


PIPELINE_STAGES: list[Stage] = [
    Stage(
        key="pool_generation",
        label="POOL GENERATION",
        logger_name="src.elt_lakehouse.spark.jobs.pool_job",
        completion_match="Pool generation completed successfully",
        jobs=[
            Job(
                "customers",
                "Customers",
                "Generating pool: customers",
                "metadata/pools/customer_pool.parquet",
            ),
            Job(
                "customer_locations",
                "Customer Locations",
                "Generating pool: customer locations",
                "metadata/pools/customer_location_pool.parquet",
            ),
            Job(
                "sellers",
                "Sellers",
                "Generating pool: sellers",
                "metadata/pools/seller_pool.parquet",
            ),
            Job(
                "products",
                "Products",
                "Generating pool: products",
                "metadata/pools/product_pool.parquet",
            ),
        ],
    ),
    Stage(
        key="dataset_generation",
        label="DATASET GENERATION",
        logger_name="src.elt_lakehouse.spark.jobs.dataset_job",
        completion_match="Dataset generation completed successfully",
        jobs=[
            Job(
                "customers",
                "Customers",
                "Generating dataset:customers",
                "storage/generated/generated_customers_data.parquet",
            ),
            Job(
                "geolocations",
                "Geolocations",
                "Generating dataset:geolocations",
                "storage/generated/generated_geolocation_data.parquet",
            ),
            Job(
                "sellers",
                "Sellers",
                "Generating dataset:sellers",
                "storage/generated/generated_sellers_data.parquet",
            ),
            Job(
                "products",
                "Products",
                "Generating dataset:products",
                "storage/generated/generated_products_data.parquet",
            ),
            Job(
                "orders",
                "Orders",
                "Generating dataset:orders",
                "storage/generated/generated_orders_data.parquet",
            ),
            Job(
                "order_items",
                "Order Items",
                "Generating dataset:order items",
                "storage/generated/generated_order_items_data.parquet",
            ),
            Job(
                "payments",
                "Payments",
                "Generating dataset:payments",
                "storage/generated/generated_payments_data.parquet",
            ),
            Job(
                "reviews",
                "Reviews",
                "Generating dataset:reviews",
                "storage/generated/generated_reviews_data.parquet",
            ),
        ],
    ),
    Stage(
        key="bronze_ingestion",
        label="BRONZE INGESTION",
        logger_name="src.elt_lakehouse.spark.jobs.bronze_job",
        completion_match="All ingestion functions completed successfully",
        jobs=[
            Job("orders", "Orders", "Order ingestion", "storage/bronze/orders_delta"),
            Job(
                "order_items",
                "Order Items",
                "order items ingestion",
                "storage/bronze/order_items_delta",
            ),
            Job(
                "payments",
                "Payments",
                "payment ingestion",
                "storage/bronze/payments_delta",
            ),
            Job(
                "reviews",
                "Reviews",
                "reviews ingestion",
                "storage/bronze/reviews_delta",
            ),
            Job(
                "sellers", "Sellers", "seller ingestion", "storage/bronze/sellers_delta"
            ),
            Job(
                "geolocation",
                "Geolocation",
                "geolocation ingestion",
                "storage/bronze/geolocation_delta",
            ),
            Job(
                "customers",
                "Customers",
                "customer ingestion",
                "storage/bronze/customers_delta",
            ),
            Job(
                "products",
                "Products",
                "product ingestion",
                "storage/bronze/products_delta",
            ),
        ],
    ),
    Stage(
        key="silver_transformation",
        label="SILVER TRANSFORMATION",
        logger_name="src.elt_lakehouse.spark.jobs.silver_job",
        completion_match="All data validations completed successfully",
        jobs=[
            Job(
                "silver_tables",
                "Silver Tables",
                "Silver layer processing",
                "storage/silver",
            ),
        ],
    ),
    Stage(
        key="gold_transformation",
        label="GOLD / DBT TRANSFORMATION",
        logger_name="src.elt_lakehouse.spark.jobs.gold_job",
        completion_match="Gold layer build completed successfully",
        jobs=[
            Job("gold_models", "Gold Models", "Gold build", "storage/gold"),
        ],
    ),
]

logger.debug("Loaded pipeline registry with %d stages", len(PIPELINE_STAGES))


STORAGE_LAYERS = [
    {
        "key": "source",
        "label": "SOURCE",
        "sublabel": "GENERATED DATA",
        "path": "storage/generated",
    },
    {
        "key": "bronze",
        "label": "BRONZE",
        "sublabel": "RAW DATA",
        "path": "storage/bronze",
    },
    {
        "key": "silver",
        "label": "SILVER",
        "sublabel": "CLEAN DATA",
        "path": "storage/silver",
    },
    {"key": "gold", "label": "GOLD", "sublabel": "ANALYTICS", "path": "storage/gold"},
]

# Kept for backward compatibility with anything still referencing the
# original two-layer name.
DOWNSTREAM_LAYERS = [
    layer for layer in STORAGE_LAYERS if layer["key"] in ("silver", "gold")
]
