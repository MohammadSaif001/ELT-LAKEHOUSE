import pandas as pd
from spark.common.logger import get_logger
from profiling_scr.common import load_csv, save_profile

logger = get_logger(__name__)
def build_order_profiles() -> None:
    """
        Build order profiling metadata from the original Olist datasets.
    
        Generates:
            - order_status_distribution.json
            - delivery_time_stats.json
            - order_approval_delay_stats.json
            - order_carrier_delay_stats.json
            - order_delivery_delay_distribution.json
            - order_purchase_month_distribution.json
            - order_purchase_weekday_distribution.json
            - order_purchase_hours_distribution.json
            - order_total_delivery_delay_distribution.json
            - order_estimated_delivery_delay_distribution.json
            - order_shipping_delay_stats.json
        """
        
    order = load_csv("olist_orders_dataset.csv")
    order_items = load_csv("olist_order_items_dataset.csv")
    
    order.columns = order.columns.str.strip().str.strip('"')
    order_items.columns = order_items.columns.str.strip().str.strip('"')
    #============================
    # Order Status Distribution
    #============================
    order_status_distribution = (
    order["order_status"].str.strip().
    value_counts(normalize=True)
    .to_dict()
    )
    
    save_profile(
        order_status_distribution,
        "order_status_distribution.json",
    )
    logger.info("Generated order status distribution")
    
    #===========================
    # Delivery Time Stats
    #===========================
    
    order["order_purchase_timestamp"] = pd.to_datetime(order["order_purchase_timestamp"], errors='coerce')
    order["order_delivered_customer_date"] = pd.to_datetime(order["order_delivered_customer_date"], errors='coerce')
    delivery_days = (
    order["order_delivered_customer_date"]
    - order["order_purchase_timestamp"]).dt.days

    stats = {
    "mean" : float(delivery_days.mean()),
    "median" : float(delivery_days.median()),
    "std" : float(delivery_days.std()),
    "min" : float(delivery_days.min()),
    "max" : float(delivery_days.max()),
    "p25" : float(delivery_days.quantile(0.25)),
    "p50" : float(delivery_days.quantile(0.50)),
    "p75" : float(delivery_days.quantile(0.75)),
    "p95" : float(delivery_days.quantile(0.95)),
    "count" : int(delivery_days.count())
            }
    
    save_profile(
        stats,
        "delivery_time_stats.json",
    )
    logger.info("Generated delivery time stats")
    
    #===========================
    # Order Approval Delay Stats
    #===========================
    date_cols = [
    "order_approved_at",
    "order_purchase_timestamp",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]


    order[date_cols] = order[date_cols].apply(
    lambda col: pd.to_datetime(col, errors="coerce")
)

    approval_delay = (
    order["order_approved_at"].astype("datetime64[ns]")
    -
    order["order_purchase_timestamp"].astype("datetime64[ns]")
    ).dt.total_seconds() / 3600

    approval_dist = {
    "mean_hours" : float(approval_delay.mean()),
    "median_hours" : float(approval_delay.median()),
    "std_hours" : float(approval_delay.std()),
    "min_hours" : float(approval_delay.min()),
    "max_hours" : float(approval_delay.max()),
    "p25_hours" : float(approval_delay.quantile(0.25)),
    "p50_hours" : float(approval_delay.quantile(0.50)),
    "p75_hours" : float(approval_delay.quantile(0.75)),
    "p95_hours" : float(approval_delay.quantile(0.95)),
    "count_hours" : int(approval_delay.count())
    }
    save_profile(
        approval_dist,
        "order_approval_delay_stats.json",
    )
    logger.info("Generated order approval delay stats")
    
    #==========================================================
    # Order Carrier Delay Stats and Delivery Delay Distribution
    #==========================================================
    carrier_delay = (
    order["order_delivered_carrier_date"]
    -
    order["order_approved_at"]
    ).dt.days.dropna()

    carrier_delay = carrier_delay[
    carrier_delay >= 0
    ]


    carrier_distribution = (
    carrier_delay
    .value_counts()
    .sort_index()
    .round(2)
    .to_dict()
    )

    carrier_stats = {
    "mean_days" : round(float(carrier_delay.mean()), 2),
    "median_days" : round(float(carrier_delay.median()), 2),
    "std_days" : round(float(carrier_delay.std()), 2),
    "min_days" : round(float(carrier_delay.min()), 2),
    "max_days" : round(float(carrier_delay.max()), 2),
    "p50_days" : float(carrier_delay.quantile(0.50)),
    "p25_days" : float(carrier_delay.quantile(0.25)),
    "p75_days" : float(carrier_delay.quantile(0.75)),
    "p95_days" : float(carrier_delay.quantile(0.95)),
    "count_days" : round(int(carrier_delay.count()), 2)
    }
    
    save_profile(
        carrier_distribution,
        "order_carrier_delay_distribution.json",
    )
    
    save_profile(
        carrier_stats,
        "order_carrier_delay_stats.json",
    )
    logger.info("Generated order carrier delay distribution and stats")
    
    #==================================
    # Order Delivery Delay Distribution
    #==================================
    delivery_delay = (
    order["order_delivered_customer_date"]
    -
    order["order_delivered_carrier_date"]
    ).dt.days.dropna()

    delivery_delay = delivery_delay[
    delivery_delay >= 0]

    delivery_delay_distribution = (
    delivery_delay
    .value_counts(normalize=True)
    .sort_index()
    .round(4)
    .to_dict()
    )
    
    save_profile(
        delivery_delay_distribution,
        "order_delivery_delay_distribution.json",
    )
    
    logger.info("Generated order delivery delay distribution")
    
    #=========================================
    # Order Purchase Month Distribution
    #=========================================
    month_distribution = (
    order["order_purchase_timestamp"].astype("datetime64[ns]")
    .dt.month
    .value_counts(normalize=True)
    .sort_index()
    .round(4)
    .to_dict()
    )
    
    save_profile(
        month_distribution,
        "order_purchase_month_distribution.json",
    )
    
    logger.info("Generated order purchase month distribution")
    
    #=========================================
    # Order Purchase Weekday Distribution
    #=========================================
    weekdays_distribution = (
    order["order_purchase_timestamp"].astype("datetime64[ns]")
    .dt.day_name()
    .value_counts(normalize=True)
    .sort_index()
    .round(4)
    .to_dict()
    )
    
    save_profile(
        weekdays_distribution,
        "order_purchase_weekday_distribution.json",
    )
    
    logger.info("Generated order purchase weekday distribution")
    
    #=========================================
    # Order Purchase Hours Distribution
    #=========================================
    hours_distribution = (
    order["order_purchase_timestamp"].astype("datetime64[ns]")
    .dt.hour
    .value_counts(normalize=True)
    .sort_index()
    .round(4)
    .to_dict()
    )
    
    save_profile(
        hours_distribution,
        "order_purchase_hours_distribution.json",
    )
    
    logger.info("Generated order purchase hours distribution")
    
    #============================================
    # Order Total Delivery Delay Distribution
    #============================================
    Total_delivery_delay  = (
    order["order_delivered_customer_date"].astype("datetime64[ns]")
    -
    order["order_purchase_timestamp"].astype("datetime64[ns]")
    ).dt.days
    
    total_delivery_delay_distribution = (
    Total_delivery_delay
    .value_counts(normalize=True)
    .sort_index()
    .round(4)
    .to_dict()
    )
    save_profile(
        total_delivery_delay_distribution,
        "order_total_delivery_delay_distribution.json",
    )
    
    logger.info("Generated order total delivery delay distribution")
    
    #============================================
    # Order Estimated Delivery Delay Distribution
    #============================================
    estimated_delivery_delay = (
    order["order_estimated_delivery_date"].astype("datetime64[ns]")
    -
    order["order_purchase_timestamp"].astype("datetime64[ns]")
    ).dt.days

    estimated_delivery_delay_distribution = (
    estimated_delivery_delay
    .value_counts(normalize=True)
    .sort_index()
    .round(4)
    .to_dict()
    )
    
    save_profile(
        estimated_delivery_delay_distribution,
        "order_estimated_delivery_delay_distribution.json",
    )
    
    logger.info("Generated order estimated delivery delay distribution")
    
    #=========================================
    # Order Shipping Delay Stats
    #=========================================
    merged = order.merge(
    order_items,on  = "order_id")

    shipping_days = (
    merged["shipping_limit_date"].astype("datetime64[ns]")
    - merged["order_purchase_timestamp"].astype("datetime64[ns]")
    ).dt.days
    
    shipping_days = shipping_days.describe().to_dict()
    
    save_profile(
        shipping_days,
        "order_shipping_delay_stats.json",
    )
    
    logger.info("Generated order shipping delay stats") 