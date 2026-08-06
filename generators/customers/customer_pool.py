from spark.common.logger import get_logger
from config.config_loader import load_yaml
from generators.base.pool_builder import build_pool
from generators.customers.customer_generator import generate_customer

logger = get_logger("generators.customers.customer_pool")

#==========================
# Build Customers Pool
#==========================

GEN_CONFIG = load_yaml("generator_config.yaml")
POOL_CONFIG = GEN_CONFIG.get("pool_sizes") or GEN_CONFIG.get("pool_size")

def build_customers_pool() -> list:
        pool_name : str = "customer_pool.json"
        CUSTOMER_POOL : int = POOL_CONFIG["customers"]
        logger.info("Generating customer pool : size = %d " ,CUSTOMER_POOL)
        customers : list = build_pool(
            generator_function = generate_customer,
            pool_name = pool_name,
            size = CUSTOMER_POOL
        )
        logger.info(
        "Customer pool generated successfully: file= %s, records= %d",
        pool_name,
        len(customers),)
        
        return customers