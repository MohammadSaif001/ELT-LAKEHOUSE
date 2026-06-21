from generators.base.pool_manger import save_pool

def build_pool(generator_function, pool_name : str, size : int):
    pool = []
    for _ in range(size):
        pool.append(generator_function())
    save_pool( pool, pool_name)
    return pool