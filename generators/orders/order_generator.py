import json
import random
from datetime import datetime
from datetime import timedelta
from generators.base.generator_base import generate_id
from generators.base.pool_manager import (
    load_pool,
)
from generators.base.distribution_loader import(
    load_distribution,
    weighted_choice,
    random_from_list
)
def get_customer_pool() -> list[dict]:
    return load_pool("customer_pool.json")


ORDER_STATUS_DIST = load_distribution( 
    "order_status_distribution.json"
)
ORDER_PURCHASE_TIMESTAMP_HOURS = load_distribution( 
    "order_purchase_hours_distribution.json"
)
ORDER_PURCHASE_TIMESTAMP_WEEKDAYS = load_distribution( 
    "order_purchase_weekdays_distribution.json"
)
ORDER_PURCHASE_TIMESTAMP_MONTHS = load_distribution( 
    "order_purchase_month_distribution.json"
)
ORDER_ESTIMATED_DELIVERY_DELAY_DIST = load_distribution( 
    "order_estimated_delivery_delay_distribution.json"
)
ORDER_CARRIER_DELAY_DIST = load_distribution( 
    "order_carrier_delay_distribution.json"
)
ORDER_DELIVERY_DELAY_DIST = load_distribution( 
    "order_delivery_delay_distribution.json"
)

ORDER_APPROVED_STATS = load_distribution(
    "order_approval_delay_stats.json"
)
def generate_order_purchase_timestamp()-> datetime:
    target_weekday = weighted_choice(ORDER_PURCHASE_TIMESTAMP_WEEKDAYS)
    weekday_map = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
        "Friday": 4, "Saturday": 5, "Sunday": 6
    }
    target_val = weekday_map[target_weekday]

    year = random_from_list([2025, 2026])
    month : int = int(weighted_choice(ORDER_PURCHASE_TIMESTAMP_MONTHS))
    day : int  = random.randint(1, 28)
    
    hour = int(weighted_choice(ORDER_PURCHASE_TIMESTAMP_HOURS))
    minute : int = random.randint(0, 59)
    second : int = random.randint(0, 59)

    dt : datetime = datetime(year, month, day, hour, minute, second)
    current_val : int = dt.weekday()
    diff : int = target_val - current_val
    dt = dt + timedelta(days=diff)

    # Cutoff at current local time June 21, 2026
    cutoff : datetime = datetime(2026, 6, 21, 13, 30)
    while dt > cutoff:
        dt = dt - timedelta(days=364) # 52 weeks preserves weekday

    return dt

def generate_approved_timestamp(purchase_timestamp: datetime) -> datetime:
    # Lognormal distribution: mean 10.42, std 26.04 -> mu = 1.35, sigma = 1.4
    delay_hours : int = round(random.lognormvariate(1.35, 1.4))
    delay_hours : int = max(1, min(720, delay_hours)) # Bound it to at most 30 days
    return purchase_timestamp + timedelta(hours=delay_hours)
    
def generate_delivered_carrier_date(approved_at : datetime) -> datetime:
    delay : float = float(
        weighted_choice(
            ORDER_CARRIER_DELAY_DIST
        )
    )
    return ( approved_at + timedelta(days=delay) )

def generate_delivered_customer_date(delivered_carrier_date: datetime) -> datetime:
    delay : float = float(
        weighted_choice(
            ORDER_DELIVERY_DELAY_DIST
        )
    )
    return ( delivered_carrier_date + timedelta(days=delay) )

def generate_estimated_delivery_date(purchase_timestamp: datetime) -> datetime:
    delay : float = float(
        weighted_choice(
            ORDER_ESTIMATED_DELIVERY_DELAY_DIST
        )
    )
    return ( purchase_timestamp + timedelta(days=delay) )
def get_customer_id() -> str:
    customer_pool = get_customer_pool()
    customer : dict = random.choice(customer_pool)
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
    
    # Estimated delivery date always exists for all orders
    estimated_delivery_date = (generate_estimated_delivery_date(purchase_timestamp))

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


