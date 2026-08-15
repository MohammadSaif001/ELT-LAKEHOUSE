from src.elt_lakehouse.generators.base.data_loading import load_generated_data

#=====================================
# Test for Null Values in Orders Data
#=====================================
def test_orders_no_null():
    orders = load_generated_data(
        "generated_orders_data.json")
    
    REQUIRED_COLUMNS:list[str] = [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp"
    ]
    
    for order in orders:
        for column in REQUIRED_COLUMNS:
            assert order[column] is not None,(
                f"Column '{column}' in order {order['order_id']} is null")

#========================================
# Test for NULL Values in Customers Data
#========================================

def test_customers_no_null():
    customers = load_generated_data(
        "generated_customers_data.json")
    REQUIRED_COLUMNS :list[str] = [
        "customer_id",
        "customer_unique_id",
        "customer_city",
        "customer_state",
        "customer_zip_code_prefix"
    ]
    for customer in customers:
        for column in REQUIRED_COLUMNS:
            assert customer[column] is not None,(
                f"Column '{column}' in customer {customer['customer_id']} is null")


#=========================================
# Test for NULL Values in Geolocation Data
#=========================================

def test_geolocations_no_null():
    geolocations = load_generated_data(
        "generated_geolocation_data.json")
    REQUIRED_COLUMNS :list[str] = [
        "customer_id",
        "geolocation_zip_code_prefix",
        "geolocation_city",
        "geolocation_state"
    ]
    
    for geolocation in geolocations:
        for column in REQUIRED_COLUMNS:
            assert geolocation[column] is not None,(
                f"Column '{column}' in geolocation {geolocation['customer_id']} is null"
            )

#=========================================
# Test for NULL Values in Seller data 
#=========================================

def test_sellers_no_null():
    sellers = load_generated_data(
        "generated_sellers_data.json")
    REQUIRED_COLUMNS :list[str]= [
        "seller_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state"
    ]
    
    for seller in sellers:
        for column in REQUIRED_COLUMNS:
            assert seller[column] is not None,(
                f"Column '{column}' in seller {seller['seller_id']} is null"
            )

#=========================================
# Test for NULL Values in Product data
#=========================================

def test_products_no_null():
    products = load_generated_data(
        "generated_products_data.json")
    REQUIRED_COLUMNS :list[str] = [
        "product_id",
        "product_category_name"
    ]
    for product in products:
        for column in REQUIRED_COLUMNS:
            assert product[column] is not None,(
                f"Column '{column}' in product {product['product_id']} is null"
            )

#=========================================
# Test for NULL Values in Order Items data
#=========================================
def test_order_items_no_null():
    order_items = load_generated_data(
        "generated_order_items_data.json")
    REQUIRED_COLUMNS :list[str]= [
        "order_id",
        "product_id"
    ]   
    for item in order_items:
        for column in REQUIRED_COLUMNS:
            assert item[column] is not None,(
                f"Column '{column}' in order item {item['order_id']} is null"
            )

#=========================================
# Test for NULL Values in Payments data
#=========================================
def test_payments_no_null():
    payments = load_generated_data(
        "generated_payments_data.json")
    
    REQUIRED_COLUMNS:list[str] = [
        "order_id",
        "payment_type",
        "payment_installments",
        "payment_value"
    ]
    
    for payment in payments:
        for column in REQUIRED_COLUMNS:
            assert payment[column] is not None,(
                f"Column '{column}' in payment {payment['order_id']} is null"
            )

#=========================================
# Test for NULL Values in Reviews data
#=========================================
def test_reviews_no_null() -> None:
    reviews = load_generated_data(
        "generated_reviews_data.json")
    REQUIRED_COLUMNS :list[str]= [
        "review_id",
        "review_score",
        "order_id"
    ]
    
    for review in reviews:
        for column in REQUIRED_COLUMNS:
            assert review[column] is not None,(
                f"Column '{column}' in review {review['review_id']} is null"
            )
