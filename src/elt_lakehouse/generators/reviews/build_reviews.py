from datetime import datetime
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.generators.base.data_loading import load_generated_data
from src.elt_lakehouse.generators.base.data_saving import save_generated_data
from src.elt_lakehouse.generators.reviews.review_generator import generate_review

logger = get_logger(__name__)

# =========================
# Review Builder
# =========================


def build_reviews(output_dir: str) -> None:
    """Generates reviews only for delivered orders and saves to generated storage."""

    orders_file: str = "generated_orders_data.json"
    output_file: str = "generated_reviews_data.json"
    started_at: datetime = datetime.now()

    try:
        logger.info("Loading generated orders: file=%s", orders_file)
        orders = load_generated_data(orders_file, base_dir=output_dir)

        delivered_orders: list = [
            order for order in orders if order["order_status"] == "delivered"
        ]

        logger.info(
            "Generating reviews: total_orders=%d, delivered_orders=%d",
            len(orders),
            len(delivered_orders),
        )

        reviews: list = [generate_review(order) for order in delivered_orders]

        logger.info(
            "Saving reviews: records=%d, file=%s, output_dir=%s",
            len(reviews),
            output_file,
            output_dir,
        )

        save_generated_data(reviews, output_file, output_dir)

        duration_seconds: float = (datetime.now() - started_at).total_seconds()
        logger.info(
            "Review dataset generated successfully: records=%d, path=%s/%s, duration_s=%.2f",
            len(reviews),
            output_dir,
            output_file,
            duration_seconds,
        )
    except Exception:
        logger.exception(
            "Review dataset generation failed: orders_file=%s, output_dir=%s",
            orders_file,
            output_dir,
        )
        raise
