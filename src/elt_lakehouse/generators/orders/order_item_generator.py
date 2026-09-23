import random
from datetime import datetime, timedelta

from src.elt_lakehouse.generators.base.distribution_loader import (
    load_distribution,
    weighted_choice,
)
from src.elt_lakehouse.generators.base.pool_manager import load_pool_column

# Price statistics
PRICE_STATS = load_distribution("order_price_stats.json")

# Freight statistics
FREIGHT_STATS = load_distribution("order_freight_value_stats.json")

# Items per order distribution
ITEMS_PER_ORDER_DIST = load_distribution("items_per_order_distribution.json")

# Shipping delay statistics
SHIPPING_STATS = load_distribution("order_shipping_delay_stats.json")


def get_product_pool() -> list[str]:
    return load_pool_column("product_pool.parquet", "product_id")


def get_seller_pool() -> list[str]:
    return load_pool_column("seller_pool.parquet", "seller_id")


def price_generator() -> float:
    """
    Generates realistic product prices using
    Olist-derived price percentiles.
    """

    r = random.random()

    if r < 0.25:
        return round(
            random.uniform(PRICE_STATS["min_price"], PRICE_STATS["p25_price"]), 2
        )

    elif r < 0.50:
        return round(
            random.uniform(PRICE_STATS["p25_price"], PRICE_STATS["p50_price"]), 2
        )

    elif r < 0.75:
        return round(
            random.uniform(PRICE_STATS["p50_price"], PRICE_STATS["p75_price"]), 2
        )

    return round(random.uniform(PRICE_STATS["p75_price"], PRICE_STATS["max_price"]), 2)


def generate_shipping_delay() -> int:
    """
    Generates realistic shipping delay in days.
    """

    while True:
        delay = round(
            random.normalvariate(SHIPPING_STATS["mean"], SHIPPING_STATS["std"])
        )

        if delay > 0:
            return delay


def generate_shipping_limit_date(purchase_timestamp: datetime) -> datetime:
    """
    Generates shipping deadline date.
    """

    delay = generate_shipping_delay()

    return purchase_timestamp + timedelta(days=delay)


def freight_value_generator() -> float:
    """
    Generates realistic freight value using
    Olist-derived freight statistics.
    """

    freight = random.normalvariate(
        FREIGHT_STATS["mean_price"], FREIGHT_STATS["std_price"]
    )

    return round(max(0.0, freight), 2)


def get_product(products: list[dict] | None = None):
    pool = products if products is not None else get_product_pool()
    return random.choice(pool)


def generate_order_item(
    order_id: str,
    order_item_id: int,
    purchase_timestamp: datetime,
    products: list[dict] | None = None,
    sellers: list[dict] | None = None,
    product: dict | str | None = None,
) -> dict:
    """
    Generates a single order item record.
    """
    product = product if product is not None else get_product(products)
    seller_pool = sellers if sellers is not None else get_seller_pool()
    seller = random.choice(seller_pool)
    product_id = product if isinstance(product, str) else product["product_id"]
    seller_id = seller if isinstance(seller, str) else seller["seller_id"]
    return {
        "order_id": order_id,
        "order_item_id": order_item_id,
        "product_id": product_id,
        "seller_id": seller_id,
        "shipping_limit_date": generate_shipping_limit_date(
            purchase_timestamp
        ).strftime("%Y-%m-%d %H:%M:%S"),
        "price": price_generator(),
        "freight_value": freight_value_generator(),
    }


# =======================
# Generate Order Items
# =======================


def generate_order_items(
    order_id: str,
    purchase_timestamp: datetime,
    products: list[dict] | None = None,
    sellers: list[dict] | None = None,
) -> list[dict]:
    """
    Generates all order items belonging
    to a single order.
    """

    num_items = int(weighted_choice(ITEMS_PER_ORDER_DIST))

    product_pool = products if products is not None else get_product_pool()
    selected_products: list[dict] = random.sample(
        product_pool,
        k=min(num_items, len(product_pool)),
    )

    return [
        generate_order_item(
            order_id=order_id,
            order_item_id=item_id,
            purchase_timestamp=purchase_timestamp,
            products=products,
            sellers=sellers,
            product=product,
        )
        for item_id, product in enumerate(selected_products, start=1)
    ]
