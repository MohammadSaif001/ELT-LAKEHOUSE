"""
Customer location generator.
Uses Olist-derived distributions and mappings to
produce realistic geolocation records.
"""
import random
from config.config_loader import load_yaml
from generators.base.distribution_loader import load_distribution


#! state distribution
state_dist = load_distribution("state_distribution.json")
#! city zip map
city_zip_map = load_distribution("city_zip_mapping.json")

#! state city map
state_city_map = load_distribution("state_city_mapping.json")

#! city coordinate map
city_coordinate_map = load_distribution("city_coordinate_mapping.json")

config = load_yaml("generator_config.yaml")["location_defaults"]

def generate_customer_location(customer: dict) -> dict:

    city : str = customer["customer_city"]
    if city not in city_coordinate_map:
        state : str = customer["customer_state"]
        state_cities : list = state_city_map.get(state, [])
        valid_cities = [cities for cities in state_cities if cities in city_coordinate_map]
        if valid_cities:
            coords = city_coordinate_map[random.choice(valid_cities)]
        else:
            fallback_coords = config.get("fallback_cordinates", {})
            coords : dict = {
                "geolocation_lat": fallback_coords.get("lat", 0.0),
                "geolocation_lng": fallback_coords.get("long", 0.0),
            }
    else:
        coords : dict = city_coordinate_map[city]

    jitter = config.get("jitter_degrees", 0.0)

    return {
        "customer_id":customer["customer_id"],
        "geolocation_zip_code_prefix":customer["customer_zip_code_prefix"],
        "geolocation_city":city,
        "geolocation_state":customer["customer_state"],

        "geolocation_lat":coords["geolocation_lat"]
            + random.uniform(-jitter, jitter),

        "geolocation_lng":coords["geolocation_lng"]
            + random.uniform(-jitter, jitter)
    }
    