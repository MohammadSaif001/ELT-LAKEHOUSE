from src.elt_lakehouse.profiling.order_profile import build_order_profiles
from src.elt_lakehouse.profiling.review_profile import build_review_profiles
from src.elt_lakehouse.profiling.seller_profile import build_seller_profiles
from src.elt_lakehouse.profiling.payment_profile import build_payment_profiles  
from src.elt_lakehouse.profiling.product_profile import build_product_profiles
from src.elt_lakehouse.profiling.customer_profile import build_customer_profiles
from src.elt_lakehouse.profiling.location_profile import build_location_profiles
from src.elt_lakehouse.profiling.order_item_profile import build_order_item_profiles



def build_profiles() -> None:
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
    
def main():
    build_profiles()
if __name__ == "__main__":
    main()