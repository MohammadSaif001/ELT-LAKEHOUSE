from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.generators.base.pool_manager import load_pool
from src.elt_lakehouse.generators.base.data_saving import save_generated_data

logger = get_logger("generators.customers.build_geolocations")
#===========================
# Geolocation Builder
#===========================

def build_geolocations(output_dir: str) -> None:
    """Load the customer location pool and save it as a generated dataset."""
    pool_name : str = "customer_location_pool.json"
    output_name : str = "generated_geolocation_data.json"
    
    try:
        logger.info("Loading customer location pool from %s", pool_name)
        locations = load_pool(pool_name)
        logger.info(
            "Saving generated geolocation dataset : records = %d , file = %s, output_dir = %s",
            len(locations),
            output_name,
            output_dir
        )
        
        save_generated_data(locations, output_name, output_dir)
        
        logger.info(
            "Geolocation dataset generated successfully: records = %d, path = %s/%s",
            len(locations),
            output_dir,
            output_name,
        )
        
    except Exception:
        logger.exception(
            "Geolocation dataset generation failed : pool = %s, output_dir = %s",
            pool_name,
            output_dir
        )
        
        raise