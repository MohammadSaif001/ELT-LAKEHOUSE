from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)
from src.elt_lakehouse.generators.base.pool_manager import save_pool


def build_pool(generator_function, pool_name: str, size: int) -> list:
    logger.info("Building pool: name=%s size=%d", pool_name, size)
    pool = []
    for _ in range(size):
        pool.append(generator_function())
    save_pool(pool, pool_name)
    logger.info("Pool built: name=%s rows=%d", pool_name, len(pool))
    return pool
