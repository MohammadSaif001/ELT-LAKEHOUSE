from spark.common.logger import get_logger
from generators.base.pool_builder import build_pool
from generators.customers.customer_generator import generate_customer

logger = get_logger("generators.customers.customer_pool")

logger.info("Customer pool generated and saved successfully to %s", "customer_pool.json")
    
def build_customers_pool() -> list:
        pool_name : str = "customer_pool.json"
        logger.info("Generating customer pool : size = %d " ,10_000)
        customers : list = build_pool(
            generator_function = generate_customer,
            pool_name = pool_name,
            size = 10_000
        )
        logger.info(
        "Customer pool generated successfully: file= %s, records= %d",
        pool_name,
        len(customers),)
        
        return customers