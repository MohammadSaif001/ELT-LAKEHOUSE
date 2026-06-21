from datetime import datetime
from generators.base.data_saving import save_generated_data
from generators.base.data_loading import load_generated_data
from generators.orders.order_generator import generate_order
from generators.orders.order_item_generator import generate_order_items

# ==========================
# Order Builder
# ==========================

def build_orders():
    """Generates order records and saves them to generated storage."""
    orders = []
    for _ in range(1000):
        orders.append(generate_order())

    save_generated_data(
        orders,
        "generated_orders_data.json"
    )

# ==========================
# Order Item Builder
# ==========================

def build_order_items():
    """Generates order item records corresponding to existing orders and saves them."""
    orders = load_generated_data(
        "generated_orders_data.json"
    )
    all_order_items = []
    for order in orders:
        purchase_timestamp = datetime.strptime(
            order["order_purchase_timestamp"],
            "%Y-%m-%d %H:%M:%S"
        )
        items = generate_order_items(
            order_id=order["order_id"],
            purchase_timestamp=purchase_timestamp
        )
        all_order_items.extend(
            items
        )
    save_generated_data(
        all_order_items,
        "generated_order_items_data.json"
    )