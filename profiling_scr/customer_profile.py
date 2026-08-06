from profiling_scr.common import load_csv, save_profile
from spark.common.logger import get_logger

logger = get_logger(__name__)


def build_customer_profiles() -> None:
    """
    Build customer profiling metadata from the original Olist datasets.

    Generates:
        - state_distribution.json
        - city_distribution.json
        - state_city_mapping.json
        - city_zip_mapping.json
        - city_coordinate_mapping.json
    """

    logger.info("Building customer profiling metadata")

    customer = load_csv("olist_customers_dataset.csv")
    geolocation = load_csv("olist_geolocation_dataset.csv")

    customer.columns = customer.columns.str.strip().str.strip('"')
    geolocation.columns = geolocation.columns.str.strip().str.strip('"')

    customer["customer_state"] = customer["customer_state"].str.strip()
    customer["customer_city"] = customer["customer_city"].str.strip()

    geolocation["geolocation_state"] = (
        geolocation["geolocation_state"]
        .str.strip()
    )

    geolocation["geolocation_city"] = (
        geolocation["geolocation_city"]
        .str.strip()
    )

    # ==========================================================
    # State distribution
    # ==========================================================

    state_distribution = (
        customer["customer_state"]
        .value_counts(normalize=True)
        .to_dict()
    )

    save_profile(
        state_distribution,
        "state_distribution.json",
    )

    logger.info("Generated state distribution")

    # ==========================================================
    # City distribution within each state
    # ==========================================================

    city_distribution = {}

    for state in customer["customer_state"].unique():

        city_distribution[state] = (
            customer.loc[
                customer["customer_state"] == state,
                "customer_city",
            ]
            .value_counts(normalize=True) # type: ignore
            .to_dict()
        )

    save_profile(
        city_distribution,
        "city_distribution.json",
    )

    logger.info("Generated city distribution")

    # ==========================================================
    # State -> Cities mapping
    # ==========================================================

    state_city_mapping = (
        geolocation.groupby("geolocation_state")[
            "geolocation_city"
        ]
        .unique()
        .apply(sorted)
        .to_dict()
    )

    save_profile(
        state_city_mapping,
        "state_city_mapping.json",
    )

    logger.info("Generated state-city mapping")

    # ==========================================================
    # City -> ZIP mapping
    # ==========================================================

    city_zip_mapping = (
        geolocation.groupby("geolocation_city")[
            "geolocation_zip_code_prefix"
        ]
        .unique()
        .apply(lambda x: sorted(map(int, x)))
        .to_dict()
    )

    save_profile(
        city_zip_mapping,
        "city_zip_mapping.json",
    )

    logger.info("Generated city-zip mapping")

    # ==========================================================
    # City -> Coordinates mapping
    # ==========================================================

    city_coordinate_mapping = (
        geolocation.groupby("geolocation_city")[
            [
                "geolocation_lat",
                "geolocation_lng",
            ]
        ]
        .mean()
        .round(6)
        .to_dict("index")
    )

    save_profile(
        city_coordinate_mapping,
        "city_coordinate_mapping.json",
    )

    logger.info("Generated city-coordinate mapping")

    logger.info("Customer profiling completed successfully")
    
if __name__ == "__main__":
    build_customer_profiles()