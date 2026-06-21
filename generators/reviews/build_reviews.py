from generators.base.data_loading import load_generated_data
from generators.base.data_saving import save_generated_data
from generators.reviews.review_generator import generate_review

def build_reviews():
    """
    Generates reviews only for delivered orders and saves to generated storage.
    """
    orders = load_generated_data("generated_orders_data.json")
    delivered_orders = [order for order in orders if order["order_status"] == "delivered"]
    
    reviews = []
    for order in delivered_orders:
        reviews.append(generate_review(order))
        
    save_generated_data(
        reviews,
        "generated_reviews_data.json"
    )
