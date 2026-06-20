from generators.base.pool_manger import save_pool
from generators.customers.customer_generator import generate_customer

#=================================
# Build Customer Pool
#================================
def build_customer_pool():
    customers = []
    for _ in range(10000):
        customers.append(generate_customer())

    save_pool(customers, "customer_pool.json")