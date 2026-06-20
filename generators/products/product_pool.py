from generators.base.pool_manger import save_pool
from generators.products.product_generator import generate_product


#==========================
# Build Product Pool
#==========================

def build_product_pool():

    products = []
    for _ in range(10000):
        products.append(
            generate_product())

    save_pool(
        products,
        "product_pool.json"
    )