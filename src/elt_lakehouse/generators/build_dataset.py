import time
from pathlib import Path
from collections.abc import Callable
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.generators.customers.build_customers import build_customers
from src.elt_lakehouse.generators.customers.build_geolocations import build_geolocations
from src.elt_lakehouse.generators.sellers.build_sellers import build_sellers
from src.elt_lakehouse.generators.products.build_products import build_products
from src.elt_lakehouse.generators.orders.build_orders import build_orders, build_order_items
from src.elt_lakehouse.generators.payments.build_payments import build_payments
from src.elt_lakehouse.generators.reviews.build_reviews import build_reviews


logger = get_logger("generators.build_dataset")
#=======================
    #Build Dataset
#=======================

def build_dataset(output_dir: str = "storage/generated") -> None:
    start_time : float = time.perf_counter()
    output_path = Path(output_dir)
    logger.info(
    "Starting dataset generation. Output directory: %s",
    output_path,)

    generators : list [tuple[str, Callable]]= [
        ("customers", build_customers),
        ("geolocations", build_geolocations),
        ("sellers", build_sellers),
        ("products", build_products),
        ("orders", build_orders),
        ("order items", build_order_items),
        ("payments", build_payments),
        ("reviews", build_reviews),
    ]
    
    try:
        for dataset_name, build_function in generators:
            logger.info("Generating dataset: %s", dataset_name)
            build_function(output_path)
            # logger.info("Dataset generated successfully: %s", dataset_name)
        elapsed : float = time.perf_counter() - start_time
        logger.info("Dataset generation completed successfully! Elapsed time: %.2f seconds", elapsed)
    except Exception:
        logger.exception("An error occurred during dataset generation.")
        raise
    

def main() -> None:
    build_dataset()
    
if __name__ == "__main__":
    main()