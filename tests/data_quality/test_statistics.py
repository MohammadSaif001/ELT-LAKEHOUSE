from collections import Counter
from generators.base.distribution_loader import load_distribution
from generators.base.data_loading import load_generated_data



def test_order_status_distribution():

    historical = load_distribution("order_status_distribution.json")

    orders = load_generated_data("generated_orders_data.json")

    counts = Counter(
        order["order_status"]
        for order in orders
    )

    total = len(orders)

    generated = {
        key: value / total
        for key, value in counts.items()
    }

    for status in historical:

        assert abs(
            generated.get(status, 0)
            -
            historical[status]
        ) < 0.05