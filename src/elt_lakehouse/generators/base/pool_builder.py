from src.elt_lakehouse.generators.base.pool_manager import save_pool


def build_pool(generator_function, pool_name: str, size: int) -> list:
    pool = []
    for _ in range(size):
        pool.append(generator_function())
    save_pool(pool, pool_name)
    return pool
