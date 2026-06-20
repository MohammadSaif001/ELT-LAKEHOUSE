from generators.base.pool_manger import load_pool, save_pool ,load_pool
from generators.customers.customer_location_generator import generate_customer_location

#=================================
# Build Customer Location Pool
#================================

def build_customer_location_pool():
    customers = load_pool(
    "customer_pool.json")

    locations = []
    for customer in customers:
        locations.append(generate_customer_location(customer))
        
    save_pool(locations,"customer_location_pool.json")