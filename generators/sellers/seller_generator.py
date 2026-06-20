import json
import random
from datetime import datetime
from datetime import timedelta
from spark.common.paths import GENETRADED_DIR
from generators.base.generator_base import generate_id
from generators.base.pool_manger import (
    load_pool,
)
from generators.base.distribution_loader import(
    load_distribution,
    weighted_choice,
    random_from_list
)

SELLER_CITY_DIST = load_distribution("seller_state_distribution.json")

SELLER_CITY_MAP = load_distribution("state_city_mapping.json")

SELLER_STATE_DIST = load_distribution("seller_state_distribution.json")

SELLER_ZIP_MAP = load_distribution("city_zip_mapping.json")


def generate_seller():
    state = weighted_choice(SELLER_STATE_DIST)
    city  = random_from_list(SELLER_CITY_MAP[state])
    zip_code = random_from_list(SELLER_ZIP_MAP[city])
    
    return {
        "seller_id": generate_id(),
        "seller_zip_code_prefix": zip_code,
        "seller_city": city,
        "seller_state": state
    }