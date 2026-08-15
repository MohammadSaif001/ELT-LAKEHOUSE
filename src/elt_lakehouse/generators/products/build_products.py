from time import perf_counter, time
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.generators.base.pool_manager import load_pool
from src.elt_lakehouse.generators.base.data_saving import save_generated_data

logger = get_logger("generators.products.build_products")

#=========================
# Product Builder  
#=========================
    

def build_products(output_dir : str) -> None:
    """Loads product pool data and saves it to the generated datasets folder."""
    pool_file : str = "product_pool.json"
    output_file : str = "generated_products_data.json"
    started_at : float = perf_counter()
    
    try:
        logger.info("Loading product pool : file = %s", pool_file)
        products = load_pool(pool_file)
        
        logger.info(
            "Saving product dataset : records = %d, file = %s, output_dir = %s",
            len(products),
            output_file,
            output_dir      
        )
        
        save_generated_data(products, output_file, output_dir)
        
        duration_seconds : float = perf_counter() - started_at
        logger.info(
            "Product dataset generated successfully: records = %d, path = %s/%s, duration = %.2f seconds",
            len(products),
            output_dir,
            output_file,
            duration_seconds
            )
    except Exception:
        logger.exception(
            "Product dataset generation failed: pool_file = %s, output_dir = %s",
            pool_file,
            output_dir,
        )
        raise