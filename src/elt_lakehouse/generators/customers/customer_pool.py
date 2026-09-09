from config.config_loader import load_yaml
from src.elt_lakehouse.generators.base.pool_builder import build_pool
from src.elt_lakehouse.generators.customers.customer_generator import generate_customer
from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)

# ==========================
# Build Customers Pool
# ==========================

GEN_CONFIG = load_yaml("generator_config.yaml")
POOL_CONFIG = GEN_CONFIG.get("pool_sizes") or GEN_CONFIG.get("pool_size")


def build_customers_pool() -> list:
    """Generate and persist the configured customer pool."""
    pool_name = "customer_pool.json"
    customer_pool_size = POOL_CONFIG["customers"]

    try:
        logger.info("Generating customer pool: size=%d", customer_pool_size)
        customers = build_pool(
            generator_function=generate_customer,
            pool_name=pool_name,
            size=customer_pool_size,
        )
        logger.info(
            "Customer pool generated successfully: file=%s, records=%d",
            pool_name,
            len(customers),
        )
        return customers
    except Exception:
        logger.exception(
            "Customer pool generation failed: pool=%s, size=%d",
            pool_name,
            customer_pool_size,
        )
        raise
