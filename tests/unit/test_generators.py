from datetime import datetime

from src.elt_lakehouse.generators.orders.order_generator import (
    generate_order,
    generate_order_purchase_timestamp,
)


def test_generate_order_purchase_timestamp() -> None:
    timestamp = generate_order_purchase_timestamp()

    assert isinstance(timestamp, datetime)


def test_generate_order() -> None:

    order: dict = generate_order()
    assert "order_id" in order
    assert "customer_id" in order
    assert "order_status" in order
