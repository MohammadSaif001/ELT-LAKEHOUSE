import pandas as pd
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.profiling.common import load_csv, save_profile

logger = get_logger(__name__)

def build_review_profiles() -> None:
    
    """
    Build review profiling metadata from the original Olist datasets.
    
        Generates:
            - review_score_distribution.json
    """
        
    review = load_csv("olist_order_reviews_dataset.csv")
    review.columns = review.columns.str.strip().str.strip('"')
    
    #===========================
    # Review Score Distribution
    #===========================
    review["review_score"] = pd.to_numeric(review["review_score"], errors="coerce")
    review_score_distribution = (
        review["review_score"]
        .dropna()
        .astype(int)
        .value_counts(normalize=True)
        .sort_index()
        .to_dict()
    )
    save_profile(
        review_score_distribution,
        "review_score_distribution.json",
    )
    logger.info("Generated review score distribution")
    
