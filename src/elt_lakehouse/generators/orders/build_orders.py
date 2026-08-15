from datetime import datetime
from config.config_loader import load_yaml
from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.generators.base.data_saving import save_generated_data
from src.elt_lakehouse.generators.base.data_loading import load_generated_data
from src.elt_lakehouse.generators.orders.order_generator import generate_order
from src.elt_lakehouse.generators.orders.order_item_generator import generate_order_items

logger = get_logger("generators.orders.build_orders")

# ==========================
# Order Builder
# ==========================

GEN_CONFIG = load_yaml("generator_config.yaml")["dataset_volume"]
def build_orders(output_dir: str) -> None:
    """Generates order records and saves them to generated storage."""
    record_count : int = GEN_CONFIG["orders"]
    output_name : str = "generated_orders_data.json"
    started_at : datetime = datetime.now()
    
    try:
        logger.info(
            "Starting order generation : records = %d, output_dir = %s",
            record_count,
            output_dir
        )
        
        orders : list = [generate_order() for _ in range(record_count)]
        
        logger.info(
            "Saving generated order dataset : records = %d , file = %s, output_dir = %s",
            len(orders),
            output_name,
            output_dir
        )
        save_generated_data(orders, output_name, output_dir)
        
        duration_seconds : float = (datetime.now() - started_at).total_seconds()
        
        logger.info(
            "Order dataset generated successfully: records = %d, path = %s/%s, duration = %.2f seconds",
            len(orders),
            output_dir,
            output_name,
            duration_seconds
        )
        
    except Exception:
        logger.exception(
            "Order dataset generation failed: output_dir=%s",
            output_dir,
        )
        raise
    pass

# ==========================
# Order Item Builder
# ==========================

def build_order_items(output_dir: str) -> None:
    """ Generates order item records corresponding to existing orders and saves them."""
    
    orders_file : str = "generated_orders_data.json"
    products_file : str = "generated_products_data.json"
    output_file : str = "generated_order_items_data.json"
    sellers_file : str = "generated_sellers_data.json"
    started_at : datetime = datetime.now()
    
    try:
        logger.info("Loading orders : file = %s", orders_file)
        orders = load_generated_data(orders_file, base_dir=output_dir)
        logger.info("Loading products : file = %s", products_file)
        products = load_generated_data(products_file, base_dir=output_dir)
        logger.info("Loading sellers : file = %s", sellers_file)
        sellers = load_generated_data(sellers_file, base_dir=output_dir)
        
        logger.info("Generating order items : records = %d", len(orders))
        all_order_items: list = []
        for order in orders:
            purchase_timestamp : datetime = datetime.strptime(
                order["order_purchase_timestamp"],
                "%Y-%m-%d %H:%M:%S"
            )
            items : list = generate_order_items(
                order_id=order["order_id"],
                purchase_timestamp=purchase_timestamp
                ,
                products=products,
                sellers=sellers
            )
            all_order_items.extend(items)
            
        logger.info(
            "Saving order-item dataset : orders = %d , records = %d , file = %s, output_dir = %s",
            len(all_order_items),
            len(orders),
            output_file,
            output_dir
        )
        save_generated_data(all_order_items, output_file, output_dir)
        
        duration_seconds : float = (datetime.now() - started_at).total_seconds()
        logger.info(
            "Order item dataset generated successfully: records = %d, path = %s/%s, duration = %.2f seconds",
            len(all_order_items),
            output_dir,
            output_file,
            duration_seconds
        )

    except Exception:
        logger.exception(
            "Order item dataset generation failed: orders_file = %s, output_dir = %s",
            orders_file,
            output_dir,
        )
        raise
