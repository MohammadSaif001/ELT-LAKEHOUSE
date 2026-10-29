from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from config.config_loader import load_yaml
from src.elt_lakehouse.generators.base.data_saving import write_tables
from src.elt_lakehouse.generators.base.parallel import (
    base_seed,
    chunk_seed,
    map_chunks,
    rows_to_table,
    seed_this_process,
    split_counts,
    worker_count,
)
from src.elt_lakehouse.generators.base.pool_manager import load_pool_column
from src.elt_lakehouse.generators.orders.order_generator import generate_order
from src.elt_lakehouse.generators.orders.order_item_generator import (
    generate_order_items,
)
from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)

ORDER_CHUNK_SIZE = 25_000  # orders generated per task
ITEM_CHUNK_ORDERS = 20_000  # orders turned into items per task

# Read-only inputs, set once per worker process by the pool initializers.
_CUSTOMER_IDS: list[str] = []
_PRODUCT_IDS: list[str] = []
_SELLER_IDS: list[str] = []


# ==========================
# Order Builder
# ==========================


def _init_order_worker(customer_ids: list[str]) -> None:
    global _CUSTOMER_IDS
    _CUSTOMER_IDS = customer_ids


def _order_chunk(task: tuple[int, int]) -> pa.Table:
    count, seed = task
    seed_this_process(seed)
    return rows_to_table(
        [generate_order(customer_ids=_CUSTOMER_IDS) for _ in range(count)]
    )


def build_orders(output_dir: str) -> None:
    """Generates order records in parallel chunks and saves them to generated storage."""
    GEN_CONFIG = load_yaml("generator_config.yaml")["dataset_volume"]
    record_count: int = GEN_CONFIG["orders"]
    output_name: str = "generated_orders_data.parquet"
    started_at: datetime = datetime.now(timezone.utc)

    try:
        logger.info(
            "Starting order generation: records=%d, output_dir=%s, workers=%d",
            record_count,
            output_dir,
            worker_count(),
        )
        customer_ids = load_pool_column("customer_pool.parquet", "customer_id")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        seed = base_seed()
        tasks = (
            (count, chunk_seed(seed, index))
            for index, count in enumerate(split_counts(record_count, ORDER_CHUNK_SIZE))
        )
        tables = map_chunks(
            _order_chunk,
            tasks,
            initializer=_init_order_worker,
            initargs=(customer_ids,),
        )
        generated_count = write_tables(tables, output_path / output_name)

        duration_seconds: float = (
            datetime.now(timezone.utc) - started_at
        ).total_seconds()

        logger.info(
            "Order dataset generated successfully: records=%d, path=%s/%s, duration_s=%.2f",
            generated_count,
            output_dir,
            output_name,
            duration_seconds,
        )

    except Exception:
        logger.exception(
            "Order dataset generation failed: output_dir=%s",
            output_dir,
        )
        raise


# ==========================
# Order Item Builder
# ==========================


def _init_item_worker(product_ids: list[str], seller_ids: list[str]) -> None:
    global _PRODUCT_IDS, _SELLER_IDS
    _PRODUCT_IDS = product_ids
    _SELLER_IDS = seller_ids


def _item_chunk(task: tuple[list[dict], int]) -> pa.Table:
    orders, seed = task
    seed_this_process(seed)
    items: list[dict] = []
    for order in orders:
        # Source timestamps are intentionally naive and follow the Olist format.
        items.extend(
            generate_order_items(
                order_id=order["order_id"],
                purchase_timestamp=datetime.fromisoformat(
                    order["order_purchase_timestamp"]
                ),
                products=_PRODUCT_IDS,
                sellers=_SELLER_IDS,
            )
        )
    return rows_to_table(items)


def _order_batches(orders_path: Path):
    """Yield (order_id, purchase_timestamp) rows from the orders file in bounded batches."""
    parquet_file = pq.ParquetFile(orders_path)
    for batch in parquet_file.iter_batches(
        batch_size=ITEM_CHUNK_ORDERS,
        columns=["order_id", "order_purchase_timestamp"],
    ):
        yield batch.to_pylist()


def build_order_items(output_dir: str) -> None:
    """Generates order item records corresponding to existing orders and saves them."""

    orders_file: str = "generated_orders_data.parquet"
    output_file: str = "generated_order_items_data.parquet"
    started_at: datetime = datetime.now(timezone.utc)

    try:
        orders_path = Path(output_dir) / orders_file
        logger.info("Loading orders: file=%s", orders_file)
        if not orders_path.exists():
            raise FileNotFoundError(f"Generated data file not found: {orders_path}")
        order_count = pq.ParquetFile(orders_path).metadata.num_rows
        logger.info("Loading product and seller IDs form pools")
        product_pool = load_pool_column("product_pool.parquet", "product_id")
        seller_pool = load_pool_column("seller_pool.parquet", "seller_id")

        logger.info(
            "Generating order items : records=%d, workers=%d",
            order_count,
            worker_count(),
        )
        seed = base_seed()
        tasks = (
            (orders, chunk_seed(seed, index))
            for index, orders in enumerate(_order_batches(orders_path))
        )
        tables = map_chunks(
            _item_chunk,
            tasks,
            initializer=_init_item_worker,
            initargs=(product_pool, seller_pool),
        )
        item_count = write_tables(tables, Path(output_dir) / output_file)

        duration_seconds: float = (
            datetime.now(timezone.utc) - started_at
        ).total_seconds()
        logger.info(
            "Order item dataset generated successfully: records=%d, path=%s/%s, duration_s=%.2f",
            item_count,
            output_dir,
            output_file,
            duration_seconds,
        )

    except Exception:
        logger.exception(
            "Order item dataset generation failed: orders_file=%s, output_dir=%s",
            orders_file,
            output_dir,
        )
        raise
