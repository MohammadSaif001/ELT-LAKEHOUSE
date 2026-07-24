from spark.common.logger import get_logger
from generators.base.pool_builder import build_pool
from generators.products.product_generator import generate_product


#==========================
# Build Product Pool
#==========================


logger = get_logger("generators.products.product_pool")

def build_product_pool() -> list:
    pool_name : str = "product_pool.json"
    logger.info("Generating product pool : size = %d " ,10_000)
    products : list = build_pool(
        generator_function = generate_product,
        pool_name = pool_name,
        size = 10_000
    )
    
    logger.info(
        "Product pool generated successfully: file= %s, records= %d",
        pool_name,
        len(products),)
    return products