from datetime import datetime
from generators.base.data_loading import load_generated_data


def test_cancelled_orders_have_no_delivery() -> None:

    orders = load_generated_data("generated_orders_data.json")
    for order in orders:
        if order["order_status"] == "canceled":
            assert (
                order["order_delivered_customer_date"]
                is None
            )


def test_delivered_orders_have_delivery_date() -> None:

    orders = load_generated_data("generated_orders_data.json")
    for order in orders:
        if order["order_status"] == "delivered": 
            assert (
                order["order_delivered_customer_date"]
                is not None
            )

def test_review_only_for_delivered_orders() -> None:

    orders = load_generated_data(
        "generated_orders_data.json"
    )
    reviews = load_generated_data(
        "generated_reviews_data.json"
    )
    order_status_map = {
        order["order_id"]: order["order_status"]
        for order in orders
    }
    for review in reviews:
        assert (
            order_status_map[
                review["order_id"]
            ] == "delivered"
        )

def test_payment_values_is_greater_than_zero() -> None:
    payments = load_generated_data("generated_payments_data.json")
    for payment in payments:
        assert payment["payment_value"] > 0
        

def test_order_have_at_least_one_item() -> None:
    
    orders = load_generated_data("generated_orders_data.json")
    order_items = load_generated_data("generated_order_items_data.json")
    item_order_ids = [
        item["order_id"] 
        for item in order_items
    ]
    for order in orders:
        if order["order_status"] != "canceled":
            assert order["order_id"] in item_order_ids,(
            f"Order {order['order_id']} has no items."
        )
    
def test_purchase_timestamps_are_valid() -> None:
    orders = load_generated_data("generated_orders_data.json")
    for order in orders:
        if order["order_status"] != "delivered":
            continue
        purchase = datetime.fromisoformat(order["order_purchase_timestamp"])
        approved = datetime.fromisoformat(order["order_approved_at"])
        delivered = datetime.fromisoformat(order["order_delivered_customer_date"])
        assert purchase <= approved <= delivered,(
            f"Timestamps for order {order['order_id']} are inconsistent: "
            f"purchase={purchase}, approved={approved}, delivered={delivered}"
        )