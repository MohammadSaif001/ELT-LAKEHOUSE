from generators.customers.customer_pool import build_customers_pool
from generators.customers.customer_location_pool import build_customer_location_pool
from generators.products.product_pool import build_product_pool
from generators.sellers.seller_pool import build_seller_pool

def main() -> None:
    print("Starting pool generation...\n")
    build_customers_pool()
    build_customer_location_pool()
    build_seller_pool()
    build_product_pool()
    print("Pool generation completed successfully!\n")
    
    
if __name__ == "__main__":
    main()