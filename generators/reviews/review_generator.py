import random
from datetime import datetime, timedelta
from generators.base.generator_base import generate_id
from generators.base.distribution_loader import (
    load_distribution,
    weighted_choice
)

# Load review score distribution
raw_score_dist = load_distribution("review_score_distribution.json")

# Filter score distribution keys 

SCORE_DIST :dict[str, float]= {key : value for key, 
            value in raw_score_dist.items()
            if key in ["1", "2", "3", "4", "5"]}
# Normalize weights

total_weight : float = sum(SCORE_DIST.values())
SCORE_DIST = {key: value/ total_weight for key, 
            value in SCORE_DIST.items()}


POSITIVE :list[tuple[str,str]] = [
    (
        "Great purchase",
        "Product arrived on time and quality was excellent."
    ),
    (
        "Excellent seller",
        "Everything arrived as expected."
    )
]

NEGATIVE :list[tuple[str,str]] = [
    (
        "Poor experience",
        "Delivery was delayed and product quality was poor."
    ),
    (
        "Disappointed",
        "Item was different from the description."
    )
]

NEUTRAL_REVIEWS :list[tuple[str,str]] = [
    (
        "Average experience",
        "Product is okay"
    ),
    (
        "Expected better",
        "Nothing special"
    )
    ]

def generate_review(order: dict) -> dict:
    """
    Generates a review record for a delivered order.
    """
    score : int = int(weighted_choice(SCORE_DIST))
    if score >= 4:
        title,message = random.choice(POSITIVE)
    elif score == 3:
        title, message = random.choice(NEUTRAL_REVIEWS)
    else:
        title, message = random.choice(NEGATIVE)
        
    # review_creation_date is 1 to 3 days after customer delivery date
    delivered_date_str = order["order_delivered_customer_date"]
    delivered_dt : datetime = datetime.strptime(delivered_date_str, "%Y-%m-%d %H:%M:%S")
    
    creation_dt : datetime = delivered_dt + timedelta(days=random.randint(1, 3))
    answer_dt : datetime = creation_dt + timedelta(days=random.randint(1, 4))
    
    return {
        "review_id": generate_id(),
        "order_id": order["order_id"],
        "review_score": score,
        "review_comment_title": title,
        "review_comment_message": message,
        "review_creation_date": creation_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "review_answer_timestamp": answer_dt.strftime("%Y-%m-%d %H:%M:%S")
    }
