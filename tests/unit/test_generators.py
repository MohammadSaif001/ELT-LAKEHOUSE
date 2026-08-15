from src.elt_lakehouse.generators.orders.order_generator import generate_order

def test_generate_order()-> None:

    order :dict = generate_order()
    assert "order_id" in order
    assert "customer_id" in order
    assert "order_status" in order