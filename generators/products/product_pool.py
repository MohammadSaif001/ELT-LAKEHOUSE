from spark.common.logger import get_logger
from config.config_loader import load_yaml
from generators.base.pool_builder import build_pool
from generators.products.product_generator import generate_product


#==========================
# Build Product Pool
#==========================

GEN_CONFIG = load_yaml("generator_config.yaml")
POOL_CONFIG = GEN_CONFIG.get("pool_sizes") or GEN_CONFIG.get("pool_size")

logger = get_logger("generators.products.product_pool")

def build_product_pool() -> list:
    pool_name : str = "product_pool.json"
    PRODUCT_POOL : int = POOL_CONFIG["products"] # type:ignore
    logger.info("Generating product pool : size = %d " ,PRODUCT_POOL)
    products : list = build_pool(
        generator_function = generate_product,
        pool_name = pool_name,
        size = PRODUCT_POOL
    )
    
    logger.info(
        "Product pool generated successfully: file= %s, records= %d",
        pool_name,
        len(products),)
    return products