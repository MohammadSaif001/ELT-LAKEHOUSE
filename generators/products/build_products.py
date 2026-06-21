from generators.base.pool_manger import load_pool
from generators.base.data_saving import save_generated_data

def build_products():
    """Loads product pool data and saves it to the generated datasets folder."""
    products = load_pool("product_pool.json")
    save_generated_data(products, "generated_products_data.json")