""" This is the main orchestration script for the ELT pipeline. 
- It generates synthetic data
- It ingests the generated data into Bronze Delta tables 
"""
import time
from generators.build_pool  import build_pool
from generators.build_dataset import data_set_builder
from ingestion.bronze.run import bronze_runner
from spark.common.logger import get_logger

logger = get_logger("elt_pipeline")

def main()-> None:
    """ Run the ELT pipeline."""
    try:
        logger.info("Starting ELT pipeline...")
        start_time = time.perf_counter()
        
        # Generate synthetic data
        build_pool()
        # data_set_builder()
        
        # Ingest data into Bronze Delta tables
        bronze_runner()
        
        elapsed_time = time.perf_counter() - start_time
        logger.info(f"ELT pipeline completed successfully in {elapsed_time:.2f} seconds.")
    except Exception :
        logger.exception(f"Pipeline failed with an critical error.")



if __name__ == "__main__":
    main()
