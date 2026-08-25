from config.config_loader import load_yaml
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.generators.base.pool_builder import build_pool
from src.elt_lakehouse.generators.sellers.seller_generator import generate_seller

# ============================
# Build Seller
# ============================

logger = get_logger(__name__)

GEN_CONFIG = load_yaml("generator_config.yaml")
POOL_CONFIG = GEN_CONFIG.get("pool_sizes") or GEN_CONFIG.get("pool_size")


def build_seller_pool() -> list:
    """Generate and persist the configured seller pool."""
    pool_name = "seller_pool.json"
    seller_pool_size = None

    try:
        seller_pool_size = POOL_CONFIG["sellers"]
        logger.info("Generating seller pool: size=%d", seller_pool_size)
        sellers = build_pool(
            generator_function=generate_seller,
            pool_name=pool_name,
            size=seller_pool_size,
        )
        logger.info(
            "Seller pool generated successfully: file=%s, records=%d",
            pool_name,
            len(sellers),
        )
        return sellers
    except Exception:
        logger.exception(
            "Seller pool generation failed: pool=%s, size=%s",
            pool_name,
            seller_pool_size,
        )
        raise
