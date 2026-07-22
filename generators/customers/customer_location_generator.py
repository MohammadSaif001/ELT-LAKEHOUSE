"""
Customer location generator.
Uses Olist-derived distributions and mappings to
produce realistic geolocation records.
"""
import random
from generators.base.distribution_loader import load_distribution


#! state distribution
state_dist = load_distribution("state_distribution.json")
#! city zip map
city_zip_map = load_distribution("city_zip_mapping.json")

#! state city map
state_city_map = load_distribution("state_city_mapping.json")

#! city coordinate map
city_coordinate_map = load_distribution("city_coordinate_mapping.json")

def generate_customer_location(customer: dict) -> dict:

    city : str = customer["customer_city"]
    if city not in city_coordinate_map:
        state : str = customer["customer_state"]
        state_cities : list = state_city_map.get(state, [])
        valid_cities = [cities for cities in state_cities if cities in city_coordinate_map]
        if valid_cities:
            coords = city_coordinate_map[random.choice(valid_cities)]
        else:
            coords : dict = {"geolocation_lat": -23.5505, "geolocation_lng": -46.6333}
    else:
        coords : dict = city_coordinate_map[city]

    return {
        "customer_id":customer["customer_id"],
        "geolocation_zip_code_prefix":customer["customer_zip_code_prefix"],
        "geolocation_city":city,
        "geolocation_state":customer["customer_state"],

        "geolocation_lat":coords["geolocation_lat"]
            + random.uniform(-0.02,0.02),

        "geolocation_lng":coords["geolocation_lng"]
            + random.uniform(-0.02,0.02)
    }
    