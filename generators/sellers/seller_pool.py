from spark.common.logger import get_logger
from generators.base.pool_builder import build_pool
from generators.sellers.seller_generator import generate_seller

#============================
# Build Seller
#============================

logger = get_logger("generators.sellers.seller_pool")

def build_seller_pool() -> list:
    pool_name : str = "seller_pool.json"
    logger.info("Generating seller pool : size = %d " ,2_000)
    sellers : list = build_pool(
        generator_function = generate_seller,
        pool_name = pool_name,
        size = 2_000)
    
    logger.info(
        "Seller pool generated successfully: file = %s, records = %d",
        pool_name,
        len(sellers),)
    return sellers
    