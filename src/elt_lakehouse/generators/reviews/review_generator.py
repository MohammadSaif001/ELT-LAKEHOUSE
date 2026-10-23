import random
from datetime import datetime, timedelta

from config.config_loader import load_yaml
from src.elt_lakehouse.generators.base.distribution_loader import (
    load_distribution,
    weighted_choice,
)
from src.elt_lakehouse.generators.base.generator_base import generate_id

# Load review score distribution
raw_score_dist = load_distribution("review_score_distribution.json")

GEN_REVIEW_CONFIG = load_yaml("generator_config.yaml")["reviews"]

# Filter score distribution keys

SCORE_DIST: dict[str, float] = {
    key: value
    for key, value in raw_score_dist.items()
    if key in ["1", "2", "3", "4", "5"]
}
# Normalize weights

total_weight: float = sum(SCORE_DIST.values())
SCORE_DIST = {key: value / total_weight for key, value in SCORE_DIST.items()}

def select_template(templates: list[dict[str, str]]) -> tuple[str, str]:
    """
    Selects a random template from the provided list of templates.
    """
    template: dict[str, str] = random.choice(templates)
    return template["title"], template["message"]


def generate_review(order: dict) -> dict:
    """
    Generates a review record for a delivered order.
    """
    score: int = int(weighted_choice(SCORE_DIST))
    if score >= GEN_REVIEW_CONFIG["positive_score_threshold"]:
        title, message = select_template(GEN_REVIEW_CONFIG["templates"]["positive"])
    elif score == GEN_REVIEW_CONFIG["neutral_score"]:
        title, message = select_template(GEN_REVIEW_CONFIG["templates"]["neutral"])
    else:
        title, message = select_template(GEN_REVIEW_CONFIG["templates"]["negative"])

    delivered_date_str = (
        order.get("order_delivered_customer_date")
        or order.get("order_estimated_delivery_date")
        or order.get("order_purchase_timestamp")
    )

    if not delivered_date_str:
        raise ValueError(
            f"Cannot generate review for order {order.get('order_id')}: missing delivery timestamp"
        )
    # Olist source timestamps are intentionally naive.
    delivered_dt: datetime = datetime.fromisoformat(delivered_date_str)

    creation_dt: datetime = delivered_dt + timedelta(
        days=random.randint(*GEN_REVIEW_CONFIG["creation_delay_days"])
    )
    answer_dt: datetime = creation_dt + timedelta(
        days=random.randint(*GEN_REVIEW_CONFIG["answer_delay_days"])
    )

    return {
        "review_id": generate_id(),
        "order_id": order["order_id"],
        "review_score": score,
        "review_comment_title": title,
        "review_comment_message": message,
        "review_creation_date": creation_dt.isoformat(sep=" ", timespec="seconds"),
        "review_answer_timestamp": answer_dt.isoformat(sep=" ", timespec="seconds"),
    }
