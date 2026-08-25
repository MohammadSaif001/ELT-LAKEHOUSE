from src.elt_lakehouse.generators.base.generator_base import generate_id
from src.elt_lakehouse.generators.base.distribution_loader import (
    load_distribution,
    weighted_choice,
    random_from_list,
)

CITY_DIST = load_distribution("city_distribution.json")
SELLER_CITY_MAP = load_distribution("state_city_mapping.json")
SELLER_STATE_DIST = load_distribution("seller_state_distribution.json")
SELLER_ZIP_MAP = load_distribution("city_zip_mapping.json")


def generate_seller() -> dict:
    """Generate a seller record with realistic location data."""
    state = weighted_choice(SELLER_STATE_DIST)
    try:
        if state in CITY_DIST and CITY_DIST[state]:
            city = weighted_choice(CITY_DIST[state])
        else:
            city = random_from_list(SELLER_CITY_MAP[state])
        zip_code = random_from_list(SELLER_ZIP_MAP.get(city, ["01000"]))

        return {
            "seller_id": generate_id(),
            "seller_zip_code_prefix": zip_code,
            "seller_city": city,
            "seller_state": state,
        }
    except Exception as exc:
        raise ValueError(f"Failed to generate seller for state: {state}") from exc
