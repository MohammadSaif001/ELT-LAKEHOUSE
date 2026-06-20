"""
Customer data generator.
Uses Olist-derived distributions and mappings to
produce realistic customer records.
"""
from generators.base.generator_base import generate_id
from generators.base.pool_manger import save_pool
from generators.base.distribution_loader import (
    load_distribution,
    weighted_choice,
    random_from_list
    )

#state distribution 
state_dist = load_distribution("state_distribution.json")

#city zip map
city_zip_map = load_distribution("city_zip_mapping.json")

#state city map
state_city_map = load_distribution("state_city_mapping.json")

def generate_customer()-> dict:
    """ Generates a customer record with realistic 
    state, city, and zip code based on Olist distributions. """

    state = weighted_choice(state_dist)
    city = random_from_list(state_city_map[state])
    zip_code = random_from_list(city_zip_map[city])

    customer = {
        "customer_id": generate_id(),
        "customer_unique_id": generate_id(),
        "customer_state": state,
        "customer_city": city,
        "customer_zip_code_prefix": zip_code
    }

    return customer
