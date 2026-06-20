import json
from spark.common.paths import GENETRADED_DIR
from generators.base.pool_manger import save_pool,load_pool
from generators.orders.order_generator import generate_order


#==========================
# Build Order Pool
#==========================

def build_order_pool():

    orders = []
    for _ in range(1000):
        orders.append(generate_order())
    with open(
        GENETRADED_DIR / "generated_orders_data.json","w") as file:
        json.dump(orders,file,indent=4)
        

#==========================
# Order Item Pool
#==========================

def build_order_item_pool():
    order_items = load_pool("generated_orders_data.json")
    with open(
        GENETRADED_DIR / "generated_order_items_data.json","w") as file:
        json.dump(order_items,file,indent=4)