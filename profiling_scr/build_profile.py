from profiling_scr.order_profile import build_order_profiles
from profiling_scr.review_profile import build_review_profiles
from profiling_scr.seller_profile import build_seller_profiles
from profiling_scr.payment_profile import build_payment_profiles  
from profiling_scr.product_profile import build_product_profiles
from profiling_scr.customer_profile import build_customer_profiles
from profiling_scr.location_profile import build_location_profiles
from profiling_scr.order_item_profile import build_order_item_profiles



def main() -> None:
    """
    Build profiling metadata for Olist datasets.
    
    Generates:
        - product profiling metadata
        - customer profiling metadata
        - location profiling metadata
        - seller profiling metadata
        - order profiling metadata
        - review profiling metadata
        - order item profiling metadata
        - payment profiling metadata
    """
    build_product_profiles()
    build_customer_profiles()
    build_location_profiles()
    build_seller_profiles()
    build_order_profiles()
    build_review_profiles()
    build_order_item_profiles()
    build_payment_profiles()
if __name__ == "__main__":
    main()