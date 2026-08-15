from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.generators.base.pool_manager import load_pool, save_pool 
from src.elt_lakehouse.generators.customers.customer_location_generator import generate_customer_location

#=================================
# Build Customer Location Pool
#=================================

logger = get_logger("generators.customers.customer_location_pool")

def build_customer_location_pool() -> None:
    customers : list = load_pool(
    "customer_pool.json")

    locations : list = []
    for customer in customers:
        locations.append(generate_customer_location(customer))
        
    save_pool(locations,"customer_location_pool.json")
    logger.info("Customer location pool generated and saved successfully to %s", "customer_location_pool.json")