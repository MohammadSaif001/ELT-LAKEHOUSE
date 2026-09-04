from src.elt_lakehouse.profiling.common import load_csv, save_profile
from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)


def build_order_item_profiles() -> None:
    """
    Build order item profiling metadata from the original Olist datasets.

        Generates:
            - items_per_order_distribution.json
            - order_item_freight_value_stats.json
            - order_item_price_stats.json
            - order_shipping_hour_distribution.json
            - order_shipping_day_distribution.json
    """

    order_items = load_csv("olist_order_items_dataset.csv")

    order_items.columns = order_items.columns.str.strip().str.strip('"')

    # ============================
    # Item per order distribution
    # ============================
    items_per_order = order_items.groupby(  # group by order id and count items
        "order_id"
    )["order_item_id"].size()

    items_dist = items_per_order.value_counts(normalize=True).sort_index().to_dict()

    save_profile(
        items_dist,
        "items_per_order_distribution.json",
    )

    # ===========================
    # Order freight value stats
    # ===========================

    stats = {
        "mean_price": float(order_items["freight_value"].mean()),
        "median_price": float(order_items["freight_value"].median()),
        "std_price": float(order_items["freight_value"].std()),
        "min_price": float(order_items["freight_value"].min()),
        "max_price": float(order_items["freight_value"].max()),
        "p25_price": float(order_items["freight_value"].quantile(0.25)),
        "p50_price": float(order_items["freight_value"].quantile(0.50)),
        "p75_price": float(order_items["freight_value"].quantile(0.75)),
        "p95_price": float(order_items["freight_value"].quantile(0.95)),
        "count_price": int(order_items["freight_value"].count()),
    }
    save_profile(
        stats,
        "order_item_freight_value_stats.json",
    )
    logger.info("Generated order item freight value stats")

    # ===========================
    # Order price stats
    # ===========================
    order_stat = {
        "mean_price": float(order_items["price"].mean()),
        "median_price": float(order_items["price"].median()),
        "std_price": float(order_items["price"].std()),
        "min_price": float(order_items["price"].min()),
        "max_price": float(order_items["price"].max()),
        "p25_price": float(order_items["price"].quantile(0.25)),
        "p50_price": float(order_items["price"].quantile(0.50)),
        "p75_price": float(order_items["price"].quantile(0.75)),
        "p95_price": float(order_items["price"].quantile(0.95)),
        "count_price": int(order_items["price"].count()),
    }
    save_profile(
        order_stat,
        "order_price_stats.json",
    )
    logger.info("Generated order item price stats")

    # =================================
    # Order shipping hour distribution
    # =================================

    order_hour_dist = (
        order_items["shipping_limit_date"]
        .astype("datetime64[ns]")
        .dt.hour.value_counts(normalize=True)
        .sort_index()
        .round(2)
        .to_dict()
    )

    save_profile(
        order_hour_dist,
        "order_shipping_hour_distribution.json",
    )
    logger.info("Generated order shipping hour distribution")

    # ====================================
    # Order shipping weekday distribution
    # ====================================
    weekday_distribution = (
        order_items["shipping_limit_date"]
        .astype("datetime64[ns]")
        .dt.day_name()
        .value_counts(normalize=True)
        .sort_index()
        .round(2)
        .to_dict()
    )
    save_profile(
        weekday_distribution,
        "order_shipping_day_distribution.json",
    )
    logger.info("Generated order shipping weekday distribution")

    # ==================================
    # Order shipping month distribution
    # ==================================
    month_distribution = (
        order_items["shipping_limit_date"]
        .astype("datetime64[ns]")
        .dt.month.value_counts(normalize=True)
        .sort_index()
        .round(4)
        .to_dict()
    )
    save_profile(
        month_distribution,
        "order_shipping_month_distribution.json",
    )
    logger.info("Generated order shipping month distribution")

    # =============================
    # Order Price Statistics
    # =============================
    order_stat = {
        "mean_price": float(order_items["price"].mean()),
        "median_price": float(order_items["price"].median()),
        "std_price": float(order_items["price"].std()),
        "min_price": float(order_items["price"].min()),
        "max_price": float(order_items["price"].max()),
        "p25_price": float(order_items["price"].quantile(0.25)),
        "p50_price": float(order_items["price"].quantile(0.50)),
        "p75_price": float(order_items["price"].quantile(0.75)),
        "p95_price": float(order_items["price"].quantile(0.95)),
        "count_price": int(order_items["price"].count()),
    }
    save_profile(
        order_stat,
        "order_price_stats.json",
    )
    logger.info("Generated order item price stats")
