import pandas as pd

from src.elt_lakehouse.profiling.common import load_csv, save_profile
from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)


def build_product_profiles() -> None:
    """
    Build product profiling metadata from the original Olist datasets.

        Generates:
            - product_category_distribution.json
            - product_weight_distribution.json
            - product_name_length_stats.json
            - product_description_length_stats.json
            - product_photos_qty_distribution.json
            - product_weight_stats.json
            - product_length_stats.json
            - product_width_stats.json
            - product_height_stats.json
    """

    product = load_csv("olist_products_dataset.csv")
    product.columns = product.columns.str.strip().str.strip('"')

    # ===========================
    # Product Category Distribution
    # ===========================
    product_category_distribution = (
        product["product_category_name"]
        .str.strip()
        .value_counts(normalize=True)
        .to_dict()
    )
    save_profile(
        product_category_distribution,
        "product_category_distribution.json",
    )
    logger.info("Product category distribution profile saved.")

    # =============================
    # Product Weight Distribution
    # =============================
    product_weight_distribution = product["product_weight_g"].describe().to_dict()
    save_profile(
        product_weight_distribution,
        "product_weight_distribution.json",
    )
    logger.info("Product weight distribution profile saved.")

    # ===============================
    # Product Name Length Statistics
    # ===============================
    name_stats = {
        "mean": float(product["product_name_lenght"].mean()),
        "median": float(product["product_name_lenght"].median()),
        "min": float(product["product_name_lenght"].min()),
        "max": float(product["product_name_lenght"].max()),
        "std": float(product["product_name_lenght"].std()),
    }
    save_profile(
        name_stats,
        "product_name_length_stats.json",
    )

    logger.info("Product name length statistics profile saved.")

    # ======================================
    # Product Description Length Statistics
    # ======================================
    description_stats = {
        "mean": float(product["product_description_lenght"].mean()),
        "median": float(product["product_description_lenght"].median()),
        "min": float(product["product_description_lenght"].min()),
        "max": float(product["product_description_lenght"].max()),
        "std": float(product["product_description_lenght"].std()),
    }
    save_profile(
        description_stats,
        "product_description_length_stats.json",
    )
    logger.info("Product description length statistics profile saved.")

    # ======================================
    # Product Description length Statistics
    # ======================================
    description_stats = {
        "mean": float(product["product_description_lenght"].mean()),
        "median": float(product["product_description_lenght"].median()),
        "min": float(product["product_description_lenght"].min()),
        "max": float(product["product_description_lenght"].max()),
        "std": float(product["product_description_lenght"].std()),
    }
    save_profile(
        description_stats,
        "product_description_length_stats.json",
    )

    logger.info("Product description length statistics profile saved.")

    # ======================================
    # Product Photo Quantity Distribution
    # ======================================
    photos_dist = (
        product["product_photos_qty"]
        .dropna()
        .value_counts(normalize=True)
        .sort_index()
        .round(4)
        .to_dict()
    )
    save_profile(
        photos_dist,
        "product_photos_qty_distribution.json",
    )
    logger.info("Product photo quantity distribution profile saved.")

    # ======================================
    # Product Weight Statistics
    # ======================================
    numeric_columns = [
        "product_weight_g",
        "product_length_cm",
        "product_width_cm",
        "product_height_cm",
    ]
    for column in numeric_columns:
        product[column] = pd.to_numeric(product[column], errors="coerce")

    weight_stats = {
        "mean": float(product["product_weight_g"].mean()),
        "median": float(product["product_weight_g"].median()),
        "min": float(product["product_weight_g"].min()),
        "max": float(product["product_weight_g"].max()),
        "std": float(product["product_weight_g"].std()),
    }
    save_profile(
        weight_stats,
        "product_weight_stats.json",
    )
    logger.info("Product weight statistics profile saved.")

    # ======================================
    # Product Length Statistics
    # ======================================
    length_stats = {
        "mean": float(product["product_length_cm"].mean()),
        "median": float(product["product_length_cm"].median()),
        "min": float(product["product_length_cm"].min()),
        "max": float(product["product_length_cm"].max()),
        "std": float(product["product_length_cm"].std()),
    }
    save_profile(
        length_stats,
        "product_length_stats.json",
    )
    logger.info("Product length statistics profile saved.")

    # ======================================
    # Product Width Statistics
    # ======================================
    width_stats = {
        "mean": float(product["product_width_cm"].mean()),
        "median": float(product["product_width_cm"].median()),
        "min": float(product["product_width_cm"].min()),
        "max": float(product["product_width_cm"].max()),
        "std": float(product["product_width_cm"].std()),
    }
    save_profile(
        width_stats,
        "product_width_stats.json",
    )
    logger.info("Product width statistics profile saved.")

    # ======================================
    # Product Height Statistics
    # ======================================

    height_stats = {
        "mean": float(product["product_height_cm"].mean()),
        "median": float(product["product_height_cm"].median()),
        "min": float(product["product_height_cm"].min()),
        "max": float(product["product_height_cm"].max()),
        "std": float(product["product_height_cm"].std()),
    }
    save_profile(
        height_stats,
        "product_height_stats.json",
    )
    logger.info("Product height statistics profile saved.")
