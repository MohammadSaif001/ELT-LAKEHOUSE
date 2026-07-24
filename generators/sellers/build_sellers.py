from time import perf_counter
from spark.common.logger import get_logger
from generators.base.pool_manager import load_pool
from generators.base.data_saving import save_generated_data

logger = get_logger("generators.sellers.build_sellers")

#=========================
# Seller Builder
#=========================

def build_sellers(output_dir: str) -> None:
    """Load the seller pool and save it as a generated dataset."""
    pool_file = "seller_pool.json"
    output_file = "generated_sellers_data.json"
    started_at = perf_counter()

    try:
        logger.info("Loading seller pool: file = %s", pool_file)
        sellers = load_pool(pool_file)

        logger.info(
            "Saving seller dataset: records = %d, file = %s, output_dir = %s",
            len(sellers),
            output_file,
            output_dir,
        )
        save_generated_data(sellers, output_file, output_dir)

        duration_seconds = perf_counter() - started_at
        logger.info(
            "Seller dataset generated successfully: records = %d, path = %s/%s, duration = %.2fs",
            len(sellers),
            output_dir,
            output_file,
            duration_seconds,
        )

    except Exception:
        logger.exception(
            "Seller dataset generation failed: pool_file = %s, output_dir = %s",
            pool_file,
            output_dir,
        )
        raise