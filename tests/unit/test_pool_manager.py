from generators.base.pool_manger import load_pool


def test_customer_pool_exists():
    customers = load_pool("customer_pool.json")
    assert len(customers) > 0