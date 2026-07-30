import time
from collections.abc import Callable
from spark.common.logger import get_logger
from generators.customers.customer_pool import build_customers_pool
from generators.customers.customer_location_pool import build_customer_location_pool
from generators.products.product_pool import build_product_pool
from generators.sellers.seller_pool import build_seller_pool

logger = get_logger("generators.build_pool")

def build_pool() -> None:
    start_time : float = time.perf_counter()
    logger.info("Starting pool generation...")
    generators: list[tuple[str, Callable]]= [
        ("customers", build_customers_pool),
        ("customer locations", build_customer_location_pool),
        ("sellers", build_seller_pool),
        ("products", build_product_pool),
    ]
    
    try:
        for pool_name, build_function in generators:
            logger.info("Generating pool: %s", pool_name)
            build_function()
        elapsed : float = time.perf_counter() - start_time
        logger.info("Pool generation completed successfully! Elapsed time: %.2f seconds", elapsed)
    except Exception:
        logger.exception("An error occurred during pool generation.")
        raise
    
    
if __name__ == "__main__":
    build_pool()