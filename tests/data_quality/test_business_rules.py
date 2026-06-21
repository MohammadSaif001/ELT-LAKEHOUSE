from generators.base.data_loading import load_generated_data


def test_cancelled_orders_have_no_delivery():

    orders = load_generated_data("generated_orders_data.json")
    for order in orders:
        if order["order_status"] == "canceled":
            assert (
                order["order_delivered_customer_date"]
                is None
            )


def test_delivered_orders_have_delivery_date():

    orders = load_generated_data("generated_orders_data.json")
    for order in orders:
        if order["order_status"] == "delivered": 
            assert (
                order["order_delivered_customer_date"]
                is not None
            )