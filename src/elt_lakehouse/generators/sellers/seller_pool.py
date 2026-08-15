from config.config_loader import load_yaml
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.generators.base.pool_builder import build_pool
from src.elt_lakehouse.generators.sellers.seller_generator import generate_seller

#============================
# Build Seller
#============================

logger = get_logger("generators.sellers.seller_pool")

GEN_CONFIG = load_yaml("generator_config.yaml")
POOL_CONFIG = GEN_CONFIG.get("pool_sizes") or GEN_CONFIG.get("pool_size")
def build_seller_pool() -> list:
    pool_name : str = "seller_pool.json"
    SELLER_POOL : int = POOL_CONFIG["sellers"]
    logger.info("Generating seller pool : size = %d " ,SELLER_POOL)
    sellers : list = build_pool(
        generator_function = generate_seller,
        pool_name = pool_name,
        size = SELLER_POOL)
    
    logger.info(
        "Seller pool generated successfully: file = %s, records = %d",
        pool_name,
        len(sellers),)
    return sellers
    