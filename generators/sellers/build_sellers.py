from generators.base.pool_manger import load_pool
from generators.base.data_saving import save_generated_data

def build_sellers(output_dir: str) -> None:
    """Loads seller pool data and saves it to the generated datasets folder."""
    sellers = load_pool("seller_pool.json")
    save_generated_data(sellers, "generated_sellers_data.json", output_dir)
