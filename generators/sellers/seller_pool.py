from generators.sellers.seller_generator import generate_seller
from generators.base.pool_manger import save_pool
from spark.common.paths import POOLS_DIR

#============================
# Build Seller Pool
#============================

def build_seller_pool():
    seller_pool = []

    for _ in range(2000):
        seller_pool.append(
        generate_seller()
    )

    save_pool(
        seller_pool,
        "seller_pool.json"
    )
