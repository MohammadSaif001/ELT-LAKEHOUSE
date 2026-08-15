"""Static description of the real ELT pipeline structure.

This mirrors elt_pipeline.py exactly (build_pool -> data_set_builder ->
bronze_runner) plus the sub-jobs each stage runs, as read from
generators/build_pool.py, generators/build_dataset.py and
ingestion/bronze/run.py. It is not invented data -- it is the fixed
topology of the pipeline, used so the dashboard can render stage/job rows
even before any run has produced log or state output.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Job:
    key: str
    label: str
    # Substrings expected in log messages for this job, used to match
    # log lines back to a specific job (see log_reader.py).
    log_match: str
    # Optional path (relative to project root) whose existence/mtime can
    # be used as a fallback signal when no log/state data is available.
    artifact_path: str | None = None


@dataclass(frozen=True)
class Stage:
    key: str
    label: str
    logger_name: str
    jobs: list[Job] = field(default_factory=list)


PIPELINE_STAGES: list[Stage] = [
    Stage(
        key="pool_generation",
        label="POOL GENERATION",
        logger_name="generators.build_pool",
        jobs=[
            Job("customers", "Customers", "Generating pool: customers",
                "metadata/pools/customer_pool.json"),
            Job("customer_locations", "Customer Locations", "Generating pool: customer locations",
                "metadata/pools/customer_location_pool.json"),
            Job("sellers", "Sellers", "Generating pool: sellers",
                "metadata/pools/seller_pool.json"),
            Job("products", "Products", "Generating pool: products",
                "metadata/pools/product_pool.json"),
        ],
    ),
    Stage(
        key="dataset_generation",
        label="DATASET GENERATION",
        logger_name="generators.build_dataset",
        jobs=[
            Job("customers", "Customers", "Generating dataset: customers",
                "storage/generated/generated_customers_data.json"),
            Job("geolocations", "Geolocations", "Generating dataset: geolocations",
                "storage/generated/generated_geolocation_data.json"),
            Job("sellers", "Sellers", "Generating dataset: sellers",
                "storage/generated/generated_sellers_data.json"),
            Job("products", "Products", "Generating dataset: products",
                "storage/generated/generated_products_data.json"),
            Job("orders", "Orders", "Generating dataset: orders",
                "storage/generated/generated_orders_data.json"),
            Job("order_items", "Order Items", "Generating dataset: order items",
                "storage/generated/generated_order_items_data.json"),
            Job("payments", "Payments", "Generating dataset: payments",
                "storage/generated/generated_payments_data.json"),
            Job("reviews", "Reviews", "Generating dataset: reviews",
                "storage/generated/generated_reviews_data.json"),
        ],
    ),
    Stage(
        key="bronze_ingestion",
        label="BRONZE INGESTION",
        logger_name="ingestion.bronze.run",
        jobs=[
            Job("orders", "Orders", "Order ingestion",
                "storage/bronze/orders_delta"),
            Job("order_items", "Order Items", "order item ingestion",
                "storage/bronze/order_items_delta"),
            Job("payments", "Payments", "payment ingestion",
                "storage/bronze/payments_delta"),
            Job("reviews", "Reviews", "review ingestion",
                "storage/bronze/reviews_delta"),
            Job("sellers", "Sellers", "seller ingestion",
                "storage/bronze/sellers_delta"),
            Job("geolocation", "Geolocation", "geolocation ingestion",
                "storage/bronze/geolocation_delta"),
            Job("customers", "Customers", "customer ingestion",
                "storage/bronze/customers_delta"),
        ],
    ),
]


DOWNSTREAM_LAYERS = [
    {"key": "silver", "label": "SILVER LAYER", "path": "storage/silver"},
    {"key": "gold", "label": "GOLD LAYER", "path": "storage/gold"},
]
