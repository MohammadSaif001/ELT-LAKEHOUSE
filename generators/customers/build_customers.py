from generators.base.pool_manager import load_pool
from generators.base.data_saving import save_generated_data

def build_customers(output_dir: str) -> None:
    """Loads customer pool data and saves it to the generated datasets folder."""
    customers = load_pool("customer_pool.json")
    save_generated_data(customers, "generated_customers_data.json", output_dir)
