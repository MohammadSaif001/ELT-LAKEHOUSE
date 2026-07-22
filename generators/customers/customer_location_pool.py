from generators.base.pool_manager import load_pool, save_pool 
from generators.customers.customer_location_generator import generate_customer_location

#=================================
# Build Customer Location Pool
#================================

def build_customer_location_pool() -> None:
    customers : list = load_pool(
    "customer_pool.json")

    locations : list = []
    for customer in customers:
        locations.append(generate_customer_location(customer))
        
    save_pool(locations,"customer_location_pool.json")