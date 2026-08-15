from src.elt_lakehouse.generators.base.generator_base import generate_id
from src.elt_lakehouse.generators.base.distribution_loader import (
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

# city distribution
city_dist = load_distribution("city_distribution.json")

def generate_customer()-> dict:
    """ Generates a customer record with realistic 
    state, city, and zip code based on Olist distributions. """

    state = weighted_choice(state_dist)
    if state in city_dist and city_dist[state]:
        city = weighted_choice(city_dist[state])
    else:
        city = random_from_list(state_city_map[state])
    zip_code = str(
        random_from_list(city_zip_map.get(city, ["01000"]))
        )

    customer = {
        "customer_id": generate_id(),
        "customer_unique_id": generate_id(),
        "customer_state": state,
        "customer_city": city,
        "customer_zip_code_prefix": zip_code
    }

    return customer
