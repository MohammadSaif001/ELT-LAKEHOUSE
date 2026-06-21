from generators.base.pool_builder import build_pool
from generators.products.product_generator import generate_product


#==========================
# Build Product Pool
#==========================

def build_product():
    return build_pool(
        generator_function = generate_product,
        pool_name = "product_pool.json",
        size = 10000  
    )