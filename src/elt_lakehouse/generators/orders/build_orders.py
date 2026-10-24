import os
import sys
import tempfile
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

from config.config_loader import load_yaml
from src.elt_lakehouse.generators.base.data_loading import load_generated_data
from src.elt_lakehouse.generators.base.data_saving import (
    save_generated_batches,
    save_generated_data,
)
from src.elt_lakehouse.generators.orders.order_generator import generate_order
from src.elt_lakehouse.generators.orders.order_item_generator import (
    generate_order_items,
)
from src.elt_lakehouse.generators.base.pool_manager import load_pool_column
from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)

ORDER_BATCH_SIZE = 20_000
ORDER_MAX_WORKERS = 4


def _order_batches(
    customer_ids: list[str], record_count: int, batch_size: int
) -> Iterator[list[dict]]:
    for batch_start in range(0, record_count, batch_size):
        batch_count = min(batch_size, record_count - batch_start)
        yield [
            generate_order(customer_ids=customer_ids) for _ in range(batch_count)
        ]


def _write_order_shard(args: tuple[int, int, str, list[str]]) -> tuple[str, int]:
    shard_index, record_count, shard_dir, customer_ids = args
    worker_count = min(ORDER_MAX_WORKERS, max(1, os.cpu_count() or 1))
    shard_start = record_count * shard_index // worker_count
    shard_end = record_count * (shard_index + 1) // worker_count
    shard_count = shard_end - shard_start
    shard_name = f"orders-part-{shard_index}.parquet"
    shard_dir_path = Path(shard_dir)

    written_rows = save_generated_batches(
        _order_batches(customer_ids, shard_count, ORDER_BATCH_SIZE),
        shard_name,
        str(shard_dir_path),
    )
    return str(shard_dir_path / shard_name), written_rows


def _merge_order_shards(shards: list[tuple[str, int]], output_path: Path) -> int:
    writer = None
    row_count = 0
    try:
        for shard_path, _ in shards:
            parquet_file = pq.ParquetFile(shard_path)
            for record_batch in parquet_file.iter_batches(batch_size=65_536):
                if writer is None:
                    writer = pq.ParquetWriter(output_path, record_batch.schema)
                writer.write_batch(record_batch)
                row_count += record_batch.num_rows
    finally:
        if writer is not None:
            writer.close()
    return row_count

# ==========================
# Order Builder
# ==========================


def build_orders(output_dir: str) -> None:
    """Generates order records and saves them to generated storage."""
    GEN_CONFIG = load_yaml("generator_config.yaml")["dataset_volume"]
    record_count: int = GEN_CONFIG["orders"]
    output_name: str = "generated_orders_data.parquet"
    started_at: datetime = datetime.now(timezone.utc)

    try:
        logger.info(
            "Starting order generation: records=%d, output_dir=%s",
            record_count,
            output_dir,
        )
        customer_ids = load_pool_column("customer_pool.parquet", "customer_id")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        gil_enabled = getattr(sys, "_is_gil_enabled", lambda: True)()
        worker_count = min(ORDER_MAX_WORKERS, max(1, os.cpu_count() or 1))

        if not gil_enabled and worker_count > 1 and record_count >= ORDER_BATCH_SIZE * worker_count:
            with tempfile.TemporaryDirectory(
                prefix=".orders-", dir=output_path
            ) as shard_dir:
                shard_tasks = [
                    (index, record_count, shard_dir, customer_ids)
                    for index in range(worker_count)
                ]
                with ThreadPoolExecutor(max_workers=worker_count) as executor:
                    shards = list(executor.map(_write_order_shard, shard_tasks))
                generated_count = _merge_order_shards(
                    shards, output_path / output_name
                )
        else:
            generated_count = save_generated_batches(
                _order_batches(customer_ids, record_count, ORDER_BATCH_SIZE),
                output_name,
                str(output_path),
            )

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


def build_order_items(output_dir: str) -> None:
    """Generates order item records corresponding to existing orders and saves them."""

    orders_file: str = "generated_orders_data.parquet" 
    output_file: str = "generated_order_items_data.parquet"
    started_at: datetime = datetime.now(timezone.utc)

    try:
        logger.info("Loading orders: file=%s", orders_file)
        orders = load_generated_data(orders_file, base_dir=output_dir)
        logger.info("Loading product and seller IDs form pools")
        product_pool = load_pool_column("product_pool.parquet", "product_id")
        seller_pool = load_pool_column("seller_pool.parquet", "seller_id")

        logger.info("Generating order items : records=%d", len(orders))
        all_order_items: list = []
        for order in orders:
            # Source timestamps are intentionally naive and follow the Olist format.
            purchase_timestamp: datetime = datetime.fromisoformat(
                order["order_purchase_timestamp"]
            )
            items: list = generate_order_items(
                order_id=order["order_id"],
                purchase_timestamp=purchase_timestamp,
                products=product_pool,
                sellers=seller_pool,
            )
            all_order_items.extend(items)

        logger.info(
            "Saving order-item dataset: orders=%d , records=%d , file=%s, output_dir=%s",
            len(orders),
            len(all_order_items),
            output_file,
            output_dir,
        )
        save_generated_data(all_order_items, output_file, output_dir)

        duration_seconds: float = (
            datetime.now(timezone.utc) - started_at
        ).total_seconds()
        logger.info(
            "Order item dataset generated successfully: records=%d, path=%s/%s, duration_s=%.2f",
            len(all_order_items),
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
