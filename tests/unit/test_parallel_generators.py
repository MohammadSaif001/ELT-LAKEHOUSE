"""Tests for the process-parallel, chunked generators."""

import random

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.elt_lakehouse.generators.base import parallel, pool_builder, pool_manager
from src.elt_lakehouse.generators.base.data_saving import write_tables
from src.elt_lakehouse.generators.customers.customer_generator import generate_customer
from src.elt_lakehouse.generators.orders import build_orders as bo
from src.elt_lakehouse.generators.products.product_generator import generate_product
from src.elt_lakehouse.generators.reviews import build_reviews as br
from src.elt_lakehouse.generators.sellers.seller_generator import generate_seller


def _draw(task):
    count, seed = task
    parallel.seed_this_process(seed)
    return [random.random() for _ in range(count)]


def _tasks(n_chunks, size=50, base=7):
    return [(size, parallel.chunk_seed(base, i)) for i in range(n_chunks)]


def test_split_counts():
    assert parallel.split_counts(10, 4) == [4, 4, 2]
    assert parallel.split_counts(8, 4) == [4, 4]
    assert parallel.split_counts(0, 4) == []


def test_chunks_use_different_random_streams():
    chunks = list(parallel.map_chunks(_draw, _tasks(6), workers=3))
    flat = [x for chunk in chunks for x in chunk]
    assert len(flat) == 300
    assert len(set(flat)) == 300  # no worker repeated another worker's sequence


def test_results_keep_task_order_and_match_serial():
    parallel_out = list(parallel.map_chunks(_draw, _tasks(8), workers=4))
    serial_out = list(parallel.map_chunks(_draw, _tasks(8), workers=1))
    assert parallel_out == serial_out


def test_seed_env_makes_run_reproducible(monkeypatch):
    monkeypatch.setenv("GENERATOR_SEED", "123")
    assert parallel.base_seed() == parallel.base_seed() == 123
    monkeypatch.delenv("GENERATOR_SEED")
    assert parallel.base_seed() != parallel.base_seed()


def test_worker_count_env_and_default(monkeypatch):
    monkeypatch.setenv("GENERATOR_WORKERS", "3")
    assert parallel.worker_count() == 3
    monkeypatch.delenv("GENERATOR_WORKERS")
    assert 1 <= parallel.worker_count() <= parallel.MAX_DEFAULT_WORKERS


def test_write_tables_casts_all_null_chunk(tmp_path):
    first = pa.table({"a": pa.array(["x"], pa.string())})
    second = pa.table({"a": pa.array([None], pa.null())})
    path = tmp_path / "t.parquet"
    assert write_tables([first, second], path) == 2
    assert pq.read_table(path).num_rows == 2


@pytest.fixture
def small_world(tmp_path, monkeypatch):
    pools = tmp_path / "pools"
    pools.mkdir()
    monkeypatch.setenv("GENERATOR_WORKERS", "2")
    monkeypatch.setattr(pool_builder, "POOLS_DIR", pools)
    monkeypatch.setattr(pool_builder, "POOL_CHUNK_SIZE", 40)
    monkeypatch.setattr(pool_manager._pool_loader, "pools_dir", pools)
    pool_manager._pool_loader._column_cache.clear()
    pool_manager._pool_loader._pool_cache.clear()
    monkeypatch.setattr(bo, "ORDER_CHUNK_SIZE", 70)
    monkeypatch.setattr(bo, "ITEM_CHUNK_ORDERS", 60)
    monkeypatch.setattr(br, "REVIEW_CHUNK_ORDERS", 60)
    monkeypatch.setattr(
        bo, "load_yaml", lambda name: {"dataset_volume": {"orders": 400}}
    )
    return tmp_path


def test_full_generation_flow(small_world):
    assert (
        pool_builder.build_pool(generate_customer, "customer_pool.parquet", 130) == 130
    )
    assert pool_builder.build_pool(generate_product, "product_pool.parquet", 90) == 90
    assert pool_builder.build_pool(generate_seller, "seller_pool.parquet", 50) == 50

    customers = pq.read_table(small_world / "pools" / "customer_pool.parquet")
    assert len(set(customers["customer_id"].to_pylist())) == 130

    out = str(small_world / "generated")
    bo.build_orders(out)
    bo.build_order_items(out)
    br.build_reviews(out)

    orders = pq.read_table(f"{out}/generated_orders_data.parquet").to_pylist()
    items = pq.read_table(f"{out}/generated_order_items_data.parquet").to_pylist()
    reviews = pq.read_table(f"{out}/generated_reviews_data.parquet").to_pylist()

    assert len(orders) == 400
    assert len({o["order_id"] for o in orders}) == 400
    assert {i["order_id"] for i in items} <= {o["order_id"] for o in orders}
    assert {i["order_id"] for i in items} == {o["order_id"] for o in orders}
    assert all(i["order_item_id"] >= 1 for i in items)

    delivered = {o["order_id"] for o in orders if o["order_status"] == "delivered"}
    assert delivered, "test data should contain delivered orders"
    assert {r["order_id"] for r in reviews} == delivered
    assert len({r["review_id"] for r in reviews}) == len(reviews)
