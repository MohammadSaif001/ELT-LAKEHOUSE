from time import perf_counter
from spark.common.logger import get_logger
from config.config_loader import load_yaml
from generators.base.data_loading import load_generated_data
from generators.base.data_saving import save_generated_data
from generators.payments.payment_generator import generate_payment

logger = get_logger("generators.payments.build_payments")

#=========================
# Payment Builder
#=========================

GEN_CONFIG = load_yaml("generator_config.yaml")["payments"]

def build_payments(output_dir: str) -> None:
    """Generate payment records for generated orders and save them."""
    orders_file : str = "generated_orders_data.json"
    order_items_file : str = "generated_order_items_data.json"
    output_file : str = "generated_payments_data.json"
    started_at : float = perf_counter()
    FALLBACK_TOTAL : int = GEN_CONFIG["fallback_total_value"]

    try:
        logger.info(
            "Loading payment inputs: orders_file = %s, order_items_file = %s",
            orders_file,
            order_items_file,
        )
        orders = load_generated_data(orders_file, base_dir=output_dir)
        order_items = load_generated_data(order_items_file, base_dir=output_dir)

        logger.info(
            "Calculating order totals: orders = %d, order_items = %d",
            len(orders),
            len(order_items),
        )
        order_totals: dict[str, float] = {}

        for item in order_items:
            order_id = item["order_id"]
            item_total = item["price"] + item["freight_value"]
            order_totals[order_id] = order_totals.get(order_id, 0.0) + item_total

        payments: list = []
        fallback_count = 0

        for order in orders:
            order_id = order["order_id"]
            total_value = order_totals.get(order_id, 0.0)

            if total_value <= 0:
                total_value = FALLBACK_TOTAL
                fallback_count += 1

            payments.append(generate_payment(order, total_value))

        logger.info(
            "Saving payments: records = %d, fallback_payments = %d, file = %s",
            len(payments),
            fallback_count,
            output_file,
        )
        save_generated_data(payments, output_file, output_dir)

        duration_seconds : float = perf_counter() - started_at
        logger.info(
            "Payment dataset generated successfully: records = %d, path = %s/%s, duration = %.2fs",
            len(payments),
            output_dir,
            output_file,
            duration_seconds,
        )

    except Exception:
        logger.exception(
            "Payment dataset generation failed: orders_file = %s, output_dir = %s",
            orders_file,
            output_dir,
        )
        raise