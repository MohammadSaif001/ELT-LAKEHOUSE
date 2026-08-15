from src.elt_lakehouse.generators.base.pool_manager import load_pool


def test_customer_pool_exists() -> None:
    customers = load_pool("customer_pool.json")
    assert len(customers) > 0