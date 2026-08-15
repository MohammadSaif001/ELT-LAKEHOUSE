import time
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.generators.build_pool  import build_pool
from src.elt_lakehouse.generators.build_dataset import build_dataset
from src.elt_lakehouse.ingestion.bronze.bronze_runner import bronze_runner
logger = get_logger("elt_pipeline")

#==========================
        #ELT Pipeline
#==========================

def orchestrate() -> None:
    """ Run the ELT pipeline."""
    try:
        logger.info("Starting ELT pipeline...")
        start_time = time.perf_counter()
        
        # Generate synthetic data
        build_pool()
        
        # Generate datasets from the synthetic data
        build_dataset()
        
        # Ingest data into Bronze Delta tables
        bronze_runner()
        
        elapsed_time = time.perf_counter() - start_time
        logger.info(f"ELT pipeline completed successfully in {elapsed_time:.2f} seconds.")
    except Exception :
        logger.exception(f"Pipeline failed with an critical error.")

def main() -> None:
    """Main function to run the ELT pipeline."""
    orchestrate()


if __name__ == "__main__":
    main()
