from generators.base.data_loading import load_generated_data


def test_order_customer_fk(): #1
    customers = load_generated_data("generated_customers_data.json")
    orders = load_generated_data("generated_orders_data.json")

    customer_ids = {
        customer["customer_id"]
        for customer in customers
    }

    for order in orders:

        assert (
            order["customer_id"]
            in customer_ids
        )


def test_order_item_order_fk(): #2
    orders = load_generated_data("generated_orders_data.json")
    items = load_generated_data("generated_order_items_data.json")

    order_ids = {
        order["order_id"]
        for order in orders
    }

    for item in items:
        assert (
            item["order_id"]
            in order_ids
        )
        
def test_customer_geolocation_fk(): #3
    customers = load_generated_data("generated_customers_data.json")
    geolocations = load_generated_data("generated_geolocation_data.json")
    
    geolocation_ids = {
        geolocation["customer_id"]
        for geolocation in geolocations
    }
    
    for customer in customers:
        assert (
            customer["customer_id"]
            in geolocation_ids
        )
        
def test_order_item_product_fk(): #4
    orders = load_generated_data("generated_orders_data.json")
    order_items = load_generated_data("generated_order_items_data.json")
    
    order_ids = {
        order["order_id"]
        for order in orders
    }
    
    for item in order_items     :
        assert (
            item["order_id"]
            in order_ids
        )
        
def test_payment_order_fk(): #5
    payments = load_generated_data("generated_payments_data.json")
    orders = load_generated_data("generated_orders_data.json")

    order_ids = {
        order["order_id"]
        for order in orders
    }

    for payment in payments:
        assert (
            payment["order_id"]
            in order_ids
        )
        
def test_review_order_fk(): #6
    reviews = load_generated_data("generated_reviews_data.json")
    orders = load_generated_data("generated_orders_data.json")

    order_ids = {
        order["order_id"]
        for order in orders
    }

    for review in reviews:
        assert (
            review["order_id"]
            in order_ids
        )