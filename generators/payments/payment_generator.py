from typing import Literal
from config.config_loader import load_yaml
from generators.base.distribution_loader import (
    load_distribution,
    weighted_choice
)

PAYMENT_TYPE_DIST = load_distribution("payment_type_distribution.json")

PAYMENT_INSTALLMENT_DIST = load_distribution("payment_installment_distribution.json")

PAYMENT_VALUE_STATS = load_distribution("payment_value_stats.json")

PAYMENT_SEQUENCE_DIST = load_distribution("payment_sequence_distribution.json")

GEN_CONFIG = load_yaml("generator_config.yaml")["payments"]

def generate_payment(order: dict, total_value: float) -> dict:
    """ Generate payment record for an order with aligned payment value. """

    payment_type = weighted_choice(PAYMENT_TYPE_DIST)
    INSTALLMENTS_TYPES = GEN_CONFIG["single_installment_types"]

    if payment_type in INSTALLMENTS_TYPES:
        installments = 1
    else:
        installments = int(
            float(
                weighted_choice(
                    PAYMENT_INSTALLMENT_DIST
                )
            )
        )

    payment_sequential : Literal[1] = 1

    return {
        "order_id": order["order_id"],
        "payment_sequential": payment_sequential,
        "payment_type": payment_type,
        "payment_installments": installments,
        "payment_value": round(total_value, 2)
    }