from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.generators.base.pool_manager import load_pool
from src.elt_lakehouse.generators.base.data_saving import save_generated_data

logger = get_logger("generators.customers.build_customers")

#===========================
# Customer Builder
#===========================



def build_customers(output_dir: str) -> None:
    """Load the customer pool and save it as a generated dataset."""
    pool_name : str = "customer_pool.json"
    output_name : str = "generated_customers_data.json"
    
    try:
        logger.info("Loading customer pool from %s", pool_name)
        customers = load_pool(pool_name)
        logger.info(
            "Saving generated customer dataset : records = %d , file = %s, output_dir = %s",
            len(customers),
            output_name,
            output_dir
        )
        
        save_generated_data(customers, output_name, output_dir)
        
        logger.info(
            "Customer dataset generated successfully: records = %d, path = %s/%s",
            len(customers),
            output_dir,
            output_name,
        )
        
    except Exception:
        logger.exception(
            "Customer dataset generation failed : pool = %s, output_dir = %s",
            pool_name,
            output_dir
        )
        
        raise