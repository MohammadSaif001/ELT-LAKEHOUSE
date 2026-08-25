import random
from config.config_loader import load_yaml
from src.elt_lakehouse.generators.base.generator_base import generate_id
from src.elt_lakehouse.generators.base.distribution_loader import (
    load_distribution,
    weighted_choice,
)

PRODUCT_CATEGORY_DIST = load_distribution("product_category_distribution.json")

PRODUCT_WEIGHT_STATS = load_distribution("product_weight_distribution.json")

PRODUCT_NAME_STATS = load_distribution("product_name_length_stats.json")

PRODUCT_DESCRIPTION_STATS = load_distribution("product_description_length_stats.json")

PRODUCT_PHOTO_STATS = load_distribution("product_photos_qty_distribution.json")

WEIGHT_STATS = load_distribution("product_weight_stats.json")

LENGTH_STATS = load_distribution("product_length_stats.json")

HEIGHT_STATS = load_distribution("product_height_stats.json")

WIDTH_STATS = load_distribution("product_width_stats.json")

GEN_DIMENSION_CONFIG = load_yaml("generator_config.yaml")["product_dimensions"]


def generate_product() -> dict:

    name_length: int = int(
        max(
            GEN_DIMENSION_CONFIG["min_value"],
            random.normalvariate(PRODUCT_NAME_STATS["mean"], PRODUCT_NAME_STATS["std"]),
        )
    )

    description_length: int = int(
        max(
            GEN_DIMENSION_CONFIG["min_value"],
            random.normalvariate(
                PRODUCT_DESCRIPTION_STATS["mean"], PRODUCT_DESCRIPTION_STATS["std"]
            ),
        )
    )
    photo_quantity: int = int(float(weighted_choice(PRODUCT_PHOTO_STATS)))

    weight: int = round(
        max(
            GEN_DIMENSION_CONFIG["min_value"],
            random.normalvariate(WEIGHT_STATS["mean"], WEIGHT_STATS["std"]),
        )
    )

    length: int = round(
        max(
            GEN_DIMENSION_CONFIG["min_value"],
            random.normalvariate(LENGTH_STATS["mean"], LENGTH_STATS["std"]),
        )
    )

    height: int = round(
        max(
            GEN_DIMENSION_CONFIG["min_value"],
            random.normalvariate(HEIGHT_STATS["mean"], HEIGHT_STATS["std"]),
        )
    )

    width: int = round(
        max(
            GEN_DIMENSION_CONFIG["min_value"],
            random.normalvariate(WIDTH_STATS["mean"], WIDTH_STATS["std"]),
        )
    )

    return {
        "product_id": generate_id(),
        "product_category_name": weighted_choice(PRODUCT_CATEGORY_DIST),
        "product_name_length": name_length,
        "product_description_length": description_length,
        "product_photo_quantity": photo_quantity,
        "product_weight_g": weight,
        "product_length_cm": length,
        "product_height_cm": height,
        "product_width_cm": width,
    }
