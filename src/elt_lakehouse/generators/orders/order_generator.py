import random
from datetime import datetime, timedelta
from config.config_loader import load_yaml
from src.elt_lakehouse.generators.base.pool_manager import load_pool
from src.elt_lakehouse.generators.base.generator_base import generate_id
from src.elt_lakehouse.generators.base.distribution_loader import(
    load_distribution,
    weighted_choice,
    random_from_list
)

# Order status distribution
ORDER_STATUS_DIST = load_distribution("order_status_distribution.json")

# Order purchase timestamp hours distributions
ORDER_PURCHASE_TIMESTAMP_HOURS = load_distribution("order_purchase_hours_distribution.json")

# Order purchase timestamp weekday distributions
ORDER_PURCHASE_TIMESTAMP_WEEKDAYS = load_distribution("order_purchase_weekdays_distribution.json")

# Order purchase timestamp month distributions
ORDER_PURCHASE_TIMESTAMP_MONTHS = load_distribution("order_purchase_month_distribution.json")

# Order estimated delivery delay distribution
ORDER_ESTIMATED_DELIVERY_DELAY_DIST = load_distribution("order_estimated_delivery_delay_distribution.json")

# Order carrier delay distribution
ORDER_CARRIER_DELAY_DIST = load_distribution("order_carrier_delay_distribution.json")

# Order delivery delay distribution
ORDER_DELIVERY_DELAY_DIST = load_distribution( "order_delivery_delay_distribution.json")

# Order approval delay distribution
ORDER_APPROVED_STATS = load_distribution("order_approval_delay_stats.json")

GEN_CONFIG = load_yaml("generator_config.yaml")

GEN_CONFIG_STATUS = GEN_CONFIG["order_status"]

DELAY_MODELS = GEN_CONFIG["delay_models"]

def get_customer_pool() -> list[dict]:
    return load_pool("customer_pool.json")

def generate_order_purchase_timestamp()-> datetime:
    target_weekday = weighted_choice(ORDER_PURCHASE_TIMESTAMP_WEEKDAYS)
    weekday_map : dict[str, int] = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
        "Friday": 4, "Saturday": 5, "Sunday": 6
    }
    target_val: int = weekday_map[target_weekday]

    YEARS : int = random_from_list(GEN_CONFIG["generation"]["years"])
    MONTH : int = int(weighted_choice(ORDER_PURCHASE_TIMESTAMP_MONTHS))
    DAYS : int  = random.randint(
        GEN_CONFIG["generation"]["day_of_month"][0], 
        GEN_CONFIG["generation"]["day_of_month"][1]
        )
    
    HOUR = int(weighted_choice(ORDER_PURCHASE_TIMESTAMP_HOURS))
    MINUTE : int = random.randint(0, 59)
    SECOND : int = random.randint(0, 59)

    dt : datetime = datetime(YEARS, MONTH, DAYS, HOUR, MINUTE, SECOND)
    current_val : int = dt.weekday()
    diff : int = target_val - current_val
    DATE : datetime = dt + timedelta(days=diff)
    DAYS : int = GEN_CONFIG["generation"]["cutoff_step_days"]
    # Cutoff at current local time June 21, 2026
    CUTOFF : datetime = datetime.fromisoformat(GEN_CONFIG["generation"]["cutoff"])
    while DATE > CUTOFF:
        DATE = DATE - timedelta(days=DAYS) # 52 weeks preserves weekday

    return DATE

def generate_approved_timestamp(purchase_timestamp: datetime) -> datetime:
    # Lognormal distribution: mean 10.42, std 26.04 -> mu = 1.35, sigma = 1.4
    MU = DELAY_MODELS["approved_delay"]["lognormal_mu"]
    SIGMA = DELAY_MODELS["approved_delay"]["lognormal_sigma"]
    MIN_HOURS = DELAY_MODELS["approved_delay"]["min_hours"]
    MAX_HOURS = DELAY_MODELS["approved_delay"]["max_hours"]

    delay_hours : int = round(random.lognormvariate(MU, SIGMA))
    delay_hours : int = max(MIN_HOURS, min(MAX_HOURS, delay_hours)) # Bound it to at most 30 days
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

    if order_status in GEN_CONFIG_STATUS["approved_or_later"]:

        approved_at = generate_approved_timestamp(purchase_timestamp)

    if order_status in GEN_CONFIG_STATUS["shipped_or_later"]:

        delivered_carrier_date = (
            generate_delivered_carrier_date(approved_at) #type: ignore
        )

    if order_status in GEN_CONFIG_STATUS["delivered"]:

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
    
if __name__ == "__main__":
    # Example usage
    order = generate_order()
    print(order)


