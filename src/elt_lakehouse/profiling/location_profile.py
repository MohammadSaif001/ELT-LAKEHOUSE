from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.profiling.common import load_csv, save_profile

logger = get_logger(__name__)

def build_location_profiles() -> None:
    """
    Build location profiling metadata from the original Olist datasets.
    
        Generates:
            - city_coordinate_mapping.json
        """
        
    location = load_csv("olist_geolocation_dataset.csv")
    location.columns = location.columns.str.strip().str.strip('"')
    #==================================
    # Location City Coordinate Mapping
    #==================================
    city_coordinate_mapping = (
    location
    .groupby("geolocation_city")
    [["geolocation_lat","geolocation_lng"]]
    .mean()
    .to_dict("index")
    )
    save_profile(
        city_coordinate_mapping,
        "city_coordinate_mapping.json"
    )
    logger.info("City coordinate mapping profile saved.")