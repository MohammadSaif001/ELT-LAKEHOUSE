from generators.base.pool_builder import build_pool
from generators.sellers.seller_generator import generate_seller

#============================
# Build Seller
#============================

def build_seller_pool() -> list:
    return build_pool(
        generator_function = generate_seller,
        pool_name = "seller_pool.json",
        size = 2000
    )
