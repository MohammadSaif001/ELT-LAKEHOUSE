from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from src.elt_lakehouse.generators.base.data_saving import write_tables
from src.elt_lakehouse.generators.base.parallel import (
    base_seed,
    chunk_seed,
    map_chunks,
    rows_to_table,
    seed_this_process,
    worker_count,
)
from src.elt_lakehouse.generators.reviews.review_generator import generate_review
from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)

REVIEW_CHUNK_ORDERS = 20_000
_ORDER_COLUMNS = [
    "order_id",
    "order_status",
    "order_purchase_timestamp",
    "order_estimated_delivery_date",
    "order_delivered_customer_date",
]

# =========================
# Review Builder
# =========================


def _review_chunk(task: tuple[list[dict], int]) -> pa.Table:
    orders, seed = task
    seed_this_process(seed)
    return rows_to_table([generate_review(order) for order in orders])


def _delivered_batches(orders_path: Path, counts: dict[str, int]):
    """Yield delivered orders in bounded batches; ``counts`` is filled as we go."""
    parquet_file = pq.ParquetFile(orders_path)
    for batch in parquet_file.iter_batches(
        batch_size=REVIEW_CHUNK_ORDERS, columns=_ORDER_COLUMNS
    ):
        counts["total"] += batch.num_rows
        delivered = batch.filter(pc.equal(batch["order_status"], "delivered"))
        counts["delivered"] += delivered.num_rows
        if delivered.num_rows:
            yield delivered.to_pylist()


def build_reviews(output_dir: str) -> None:
    """Generates reviews only for delivered orders and saves to generated storage."""

    orders_file: str = "generated_orders_data.parquet"
    output_file: str = "generated_reviews_data.parquet"
    started_at: datetime = datetime.now(timezone.utc)

    try:
        orders_path = Path(output_dir) / orders_file
        logger.info("Loading generated orders: file=%s", orders_file)
        if not orders_path.exists():
            raise FileNotFoundError(f"Generated data file not found: {orders_path}")

        logger.info("Generating reviews: workers=%d", worker_count())
        counts = {"total": 0, "delivered": 0}
        seed = base_seed()
        tasks = (
            (orders, chunk_seed(seed, index))
            for index, orders in enumerate(_delivered_batches(orders_path, counts))
        )
        review_count = write_tables(
            map_chunks(_review_chunk, tasks), Path(output_dir) / output_file
        )
        logger.info(
            "Generated reviews: total_orders=%d, delivered_orders=%d",
            counts["total"],
            counts["delivered"],
        )

        duration_seconds: float = (
            datetime.now(timezone.utc) - started_at
        ).total_seconds()
        logger.info(
            "Review dataset generated successfully: records=%d, path=%s/%s, duration_s=%.2f",
            review_count,
            output_dir,
            output_file,
            duration_seconds,
        )
    except Exception:
        logger.exception(
            "Review dataset generation failed: orders_file=%s, output_dir=%s",
            orders_file,
            output_dir,
        )
        raise
