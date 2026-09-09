from src.elt_lakehouse.generators.base.data_loading import load_generated_data


def assert_unique(values, name) -> None:
    """
    Assert that all values in the list are unique.

    Args:
        values (list): List of values to check for uniqueness.
        name (str): Name of the entity being checked (for error messages).
    """
    assert len(values) == len(set(values)), (
        f"Duplicate {name} found: {len(values) - len(set(values))}"
    )


# =====================================
# 1.Test duplicate data in customer ids
# ======================================


def test_unique_customer_ids() -> None:

    customers = load_generated_data("generated_customers_data.json")
    ids = [customer["customer_id"] for customer in customers]

    assert_unique(ids, "customer ids")


# ===================================
# 2.Test duplicate data in order items
# ===================================
def test_unique_order_items_keys() -> None:
    seen = set()
    order_items = load_generated_data("generated_order_items_data.json")
    for order_item in order_items:
        key = (order_item["order_id"], order_item["product_id"])
        assert key not in seen, f"Duplicate order item found: {key}"
        seen.add(key)


# ================================
# 3.Test duplicate data in seller
# ================================
def test_unique_seller_ids() -> None:
    sellers = load_generated_data("generated_sellers_data.json")
    ids: list = [seller["seller_id"] for seller in sellers]
    assert_unique(ids, "seller ids")


# ==================================
# 4.Test duplicate data in products
# ==================================


def test_unique_product_ids() -> None:
    products = load_generated_data("generated_products_data.json")

    product_ids = [product["product_id"] for product in products]
    assert_unique(product_ids, "product ids")


# ================================
# 5.Test duplicate data in orders
# ================================


def test_unique_order_ids() -> None:
    orders = load_generated_data("generated_orders_data.json")

    order_ids = [order["order_id"] for order in orders]
    assert_unique(order_ids, "order ids")


# =================================
# 6.Test duplicate data in reviews
# =================================


def test_unique_review_ids() -> None:
    reviews = load_generated_data("generated_reviews_data.json")

    review_ids = [review["review_id"] for review in reviews]
    assert_unique(review_ids, "review ids")


# ===================================
# 7.Test duplicate data in payments
# ===================================


def test_unique_payment_keys() -> None:
    seen = set()
    payments = load_generated_data("generated_payments_data.json")
    for payment in payments:
        key = (
            payment["payment_sequential"],
            payment["order_id"],
            payment["payment_type"],
        )
        assert key not in seen, f"Duplicate payment found: {key}"
        seen.add(key)
