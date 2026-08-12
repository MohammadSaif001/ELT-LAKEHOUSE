""" This is the main orchestration script for the ELT pipeline. 
- It generates synthetic data
- It ingests the generated data into Bronze Delta tables 
"""
import time
from spark.common.logger import get_logger
from generators.build_pool  import build_pool
from ingestion.bronze.run import bronze_runner
from generators.build_dataset import data_set_builder

logger = get_logger("elt_pipeline")

#==========================
        #ELT Pipeline
#==========================

def main()-> None:
    """ Run the ELT pipeline."""
    try:
        logger.info("Starting ELT pipeline...")
        start_time = time.perf_counter()
        
        # Generate synthetic data
        build_pool()
        
        # Generate datasets from the synthetic data
        data_set_builder()
        
        # Ingest data into Bronze Delta tables
        bronze_runner()
        
        elapsed_time = time.perf_counter() - start_time
        logger.info(f"ELT pipeline completed successfully in {elapsed_time:.2f} seconds.")
    except Exception :
        logger.exception(f"Pipeline failed with an critical error.")



if __name__ == "__main__":
    main()
