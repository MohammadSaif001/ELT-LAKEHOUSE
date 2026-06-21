from generators.base.pool_manger import load_pool
from generators.base.data_saving import save_generated_data

def build_geolocations():
    """Loads customer location pool data and saves it to the generated datasets folder."""
    locations = load_pool("customer_location_pool.json")
    save_generated_data(locations, "generated_geolocation_data.json")
