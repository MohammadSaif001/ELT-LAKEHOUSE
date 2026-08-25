from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.profiling.common import load_csv, save_profile

logger = get_logger(__name__)


def build_seller_profiles() -> None:
    """
    Build seller profiling metadata from the original Olist datasets.

        Generates:
            - seller_state_distribution.json
    """

    sellers = load_csv("olist_sellers_dataset.csv")
    sellers.columns = sellers.columns.str.strip().str.strip('"')

    # ===========================
    # Seller State Distribution
    # ===========================
    seller_state_distribution = (
        sellers["seller_state"].str.strip().value_counts(normalize=True).to_dict()
    )
    save_profile(
        seller_state_distribution,
        "seller_state_distribution.json",
    )
    logger.info("Seller state distribution profile saved.")
