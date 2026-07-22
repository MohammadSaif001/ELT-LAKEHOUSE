from generators.base.pool_builder import build_pool
from generators.customers.customer_generator import generate_customer

#==========================
# Build Customers data
#==========================

def build_customers_pool() -> list:
    return build_pool(
        generator_function = generate_customer,
        pool_name = "customer_pool.json",
        size = 10000
    )