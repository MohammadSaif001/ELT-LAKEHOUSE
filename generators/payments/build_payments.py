from generators.base.data_loading import load_generated_data
from generators.base.data_saving import save_generated_data
from generators.payments.payment_generator import generate_payment

def build_payments():
    """Generates payment records for generated orders and saves them."""
    orders = load_generated_data("generated_orders_data.json")
    order_items = load_generated_data("generated_order_items_data.json")
    
    order_totals = {}
    for item in order_items:
        order_id = item["order_id"]
        val = item["price"] + item["freight_value"]
        order_totals[order_id] = order_totals.get(order_id, 0.0) + val
        
    payments = []
    for order in orders:
        order_id = order["order_id"]
        total_value = order_totals.get(order_id, 0.0)
        if total_value <= 0:
            total_value = 20.0  # fallback
        payments.append(generate_payment(order, total_value))
        
    save_generated_data(
        payments,
        "generated_payments_data.json"
    )