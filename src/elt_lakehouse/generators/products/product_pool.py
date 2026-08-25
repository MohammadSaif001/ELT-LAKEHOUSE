from config.config_loader import load_yaml
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.generators.base.pool_builder import build_pool
from src.elt_lakehouse.generators.products.product_generator import generate_product

# ==========================
# Build Product Pool
# ==========================

GEN_CONFIG = load_yaml("generator_config.yaml")
POOL_CONFIG = GEN_CONFIG.get("pool_sizes") or GEN_CONFIG.get("pool_size")

logger = get_logger(__name__)


def build_product_pool() -> list:
    pool_name: str = "product_pool.json"
    PRODUCT_POOL: int = POOL_CONFIG["products"]
    try:
        logger.info("Generating product pool : size=%d ", PRODUCT_POOL)
        products: list = build_pool(generator_function=generate_product, pool_name=pool_name, size=PRODUCT_POOL)

        logger.info(
            "Product pool generated successfully: file=%s, records=%d",
        pool_name,
        len(products),
        )
        return products
    except Exception:
        logger.exception(
            "Product pool generation failed: pool_name=%s, size=%d",
            pool_name,
            PRODUCT_POOL,
        )
        raise