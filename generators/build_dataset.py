from generators.customers.build_customers import build_customers
from generators.customers.build_geolocations import build_geolocations
from generators.sellers.build_sellers import build_sellers
from generators.products.build_products import build_products
from generators.orders.build_orders import build_orders, build_order_items
from generators.payments.build_payments import build_payments
from generators.reviews.build_reviews import build_reviews
from generators.base.data_loading import load_generated_data

def verify_referential_integrity():
    print("Verifying referential integrity...")
    customers = load_generated_data("generated_customers_data.json")
    geolocations = load_generated_data("generated_geolocation_data.json")
    sellers = load_generated_data("generated_sellers_data.json")
    products = load_generated_data("generated_products_data.json")
    orders = load_generated_data("generated_orders_data.json")
    order_items = load_generated_data("generated_order_items_data.json")
    payments = load_generated_data("generated_payments_data.json")
    reviews = load_generated_data("generated_reviews_data.json")

    customer_ids = {c["customer_id"] for c in customers}
    seller_ids = {s["seller_id"] for s in sellers}
    product_ids = {p["product_id"] for p in products}
    order_ids = {o["order_id"] for o in orders}

    # 1. customer.customer_id -> orders.customer_id
    for order in orders:
        assert order["customer_id"] in customer_ids, f"Order {order['order_id']} references non-existent Customer {order['customer_id']}"

    # 2. customer.customer_id -> geolocation.customer_id
    for geo in geolocations:
        assert geo["customer_id"] in customer_ids, f"Geolocation entry references non-existent Customer {geo['customer_id']}"

    # 3. seller.seller_id -> product.seller_id (or order_items.seller_id -> seller.seller_id)
    has_seller_id_in_product = len(products) > 0 and "seller_id" in products[0]
    if has_seller_id_in_product:
        for p in products:
            assert p["seller_id"] in seller_ids, f"Product {p['product_id']} references non-existent Seller {p['seller_id']}"
    else:
        for item in order_items:
            assert item["seller_id"] in seller_ids, f"Order item referencing Product {item['product_id']} references non-existent Seller {item['seller_id']}"

    # 4. product.product_id -> order_items.product_id
    for item in order_items:
        assert item["product_id"] in product_ids, f"Order item referencing Order {item['order_id']} references non-existent Product {item['product_id']}"

    # 5. orders.order_id -> order_items.order_id
    for item in order_items:
        assert item["order_id"] in order_ids, f"Order item references non-existent Order {item['order_id']}"

    # 6. orders.order_id -> payments.order_id
    for payment in payments:
        assert payment["order_id"] in order_ids, f"Payment references non-existent Order {payment['order_id']}"

    # 7. orders.order_id -> reviews.order_id
    for review in reviews:
        assert review["order_id"] in order_ids, f"Review references non-existent Order {review['order_id']}"

    print("Referential integrity verification passed successfully!")

def main():
    print("Starting generation...")
    build_customers()
    build_geolocations()
    build_sellers()
    build_products()

    build_orders()
    build_order_items()
    build_payments()
    build_reviews()
    print("Generation completed successfully!")

    verify_referential_integrity()

if __name__ == "__main__":
    main()