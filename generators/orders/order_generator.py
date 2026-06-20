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
CUSTOMER_POOL = load_pool(
    "customer_pool.json"
)
ORDER_STATUS_DIST = load_distribution( #1
    "order_status_distribution.json"
)
ORDER_PURCHASE_TIMESTAMP_HOURS = load_distribution( #2
    "order_purchase_hours_distribution.json"
)
ORDER_PURCHASE_TIMESTAMP_WEEKDAYS = load_distribution( #3
    "order_purchase_weekdays_distribution.json"
)
ORDER_PURCHASE_TIMESTAMP_MONTHS = load_distribution( #4
    "order_purchase_month_distribution.json"
)
ORDER_ESTIMATED_DELIVERY_DELAY_DIST = load_distribution( #5
    "order_estimated_delivery_delay_distribution.json"
)
ORDER_CARRIER_DELAY_DIST = load_distribution( #7
    "order_carrier_delay_distribution.json"
)
ORDER_DELIVERY_DELAY_DIST = load_distribution( #8
    "order_delivery_delay_distribution.json"
)

ORDER_APPROVED_STATS = load_distribution( #9
    "order_approval_delay_stats.json"
)
def generate_order_purchase_timestamp()-> datetime:
    year = random_from_list(
        [2025,2026]
    )
    month = int(weighted_choice(
        ORDER_PURCHASE_TIMESTAMP_MONTHS
        )
    )
    day = random.randint(1, 28)  # Simplify to avoid month-end issues
    
    hour = int(
        weighted_choice(ORDER_PURCHASE_TIMESTAMP_HOURS
        )
    )

    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return datetime(year,month,day,hour,minute,second)

def generate_approved_timestamp(purchase_timestamp: datetime) -> datetime:
    delay_hours = max(
        1,
        round(
            random.normalvariate(
                ORDER_APPROVED_STATS["mean_hours"],
                ORDER_APPROVED_STATS["std_hours"]
            )
        )
    )
    return (
        purchase_timestamp + timedelta(
            hours = delay_hours
        )
    )
    
def generate_delivered_carrier_date(approved_at : datetime) -> datetime:
    delay = float(
        weighted_choice(
            ORDER_CARRIER_DELAY_DIST
        )
    )
    return ( approved_at + timedelta(days=delay) )

def generate_delivered_customer_date(delivered_carrier_date: datetime) -> datetime:
    delay = float(
        weighted_choice(
            ORDER_DELIVERY_DELAY_DIST
        )
    )
    return ( delivered_carrier_date + timedelta(days=delay) )

def generate_estimated_delivery_date(purchase_timestamp: datetime) -> datetime:
    delay = float(
        weighted_choice(
            ORDER_ESTIMATED_DELIVERY_DELAY_DIST
        )
    )
    return ( purchase_timestamp + timedelta(days=delay) )
def get_customer_id():
    customer = random.choice(CUSTOMER_POOL)
    return customer["customer_id"]

def generate_order() -> dict:

    order_status = weighted_choice(
        ORDER_STATUS_DIST
    )

    purchase_timestamp = (
        generate_order_purchase_timestamp()
    )

    approved_at = None
    delivered_carrier_date = None
    delivered_customer_date = None
    estimated_delivery_date = None

    if order_status in ["approved","processing",
                        "invoiced","shipped", "delivered"
    ]:

        approved_at = generate_approved_timestamp(purchase_timestamp)

    if order_status in [
        "shipped","delivered"
    ]:

        delivered_carrier_date = (
            generate_delivered_carrier_date(approved_at) #type: ignore
        )

    if order_status == "delivered":

        delivered_customer_date = (
            generate_delivered_customer_date(delivered_carrier_date) #type: ignore
        )

        estimated_delivery_date = (
            generate_estimated_delivery_date(purchase_timestamp) 
            )

    return {
        "order_id": generate_id(),
        "customer_id": get_customer_id(),
        "order_status": order_status,

        "order_purchase_timestamp":
            purchase_timestamp.strftime("%Y-%m-%d %H:%M:%S"),

        "order_approved_at":
            approved_at.strftime("%Y-%m-%d %H:%M:%S")
            if approved_at else None,

        "order_delivered_carrier_date":
            delivered_carrier_date.strftime("%Y-%m-%d %H:%M:%S")
            if delivered_carrier_date else None,

        "order_delivered_customer_date":
            delivered_customer_date.strftime("%Y-%m-%d %H:%M:%S")
            if delivered_customer_date else None,

        "order_estimated_delivery_date":
            estimated_delivery_date.strftime("%Y-%m-%d %H:%M:%S")
            if estimated_delivery_date else None,
    }


