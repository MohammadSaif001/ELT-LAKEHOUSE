from generators.base.pool_manager import load_pool
from generators.base.data_saving import save_generated_data

def build_geolocations(output_dir: str) -> None:
    """Loads customer location pool data and saves it to the generated datasets folder."""
    locations = load_pool("customer_location_pool.json")
    save_generated_data(locations, "generated_geolocation_data.json", output_dir)
