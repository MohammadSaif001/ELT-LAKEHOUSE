from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

#============================
# Generators
#============================

GENERTORS_DIR = PROJECT_ROOT / "generators"
CUSTOMERS_GENERATOR_DIR = GENERTORS_DIR / "customers"
ORDERS_GENERATOR_DIR = GENERTORS_DIR / "orders"
PRODUCTS_GENERATOR_DIR = GENERTORS_DIR / "products"
REVIEWS_GENERATOR_DIR = GENERTORS_DIR / "reviews"
GENETRADED_DIR = PROJECT_ROOT / "data" / "generated"

# -------------------------
# Data
# -------------------------
DATA_DIR = PROJECT_ROOT / "data"

RAW_DATA_DIR = DATA_DIR / "raw"
PROFILING_DIR = DATA_DIR / "profiling"
ORDER_ITEM_PROFILING_DIR = PROFILING_DIR / "order_item"
GENERATED_DIR = DATA_DIR / "generated"



# -------------------------
# Storage
# -------------------------

STORAGE_DIR = PROJECT_ROOT / "storage"
BRONZE_DIR = STORAGE_DIR / "bronze"
SILVER_DIR = STORAGE_DIR / "silver"
GOLD_DIR = STORAGE_DIR / "gold"

# -------------------------
# Metadata
# -------------------------

METADATA_DIR = PROJECT_ROOT / "metadata"
POOLS_DIR = METADATA_DIR / "pools"
CHECKPOINT_DIR = METADATA_DIR / "checkpoints"
WATERMARK_DIR = METADATA_DIR / "watermarks"

# -------------------------
# Config
# -------------------------

CONFIG_DIR = PROJECT_ROOT / "config"

# -------------------------
# Contracts
# -------------------------

CONTRACT_DIR = PROJECT_ROOT / "contracts"
def get_raw_data_path(filename: str) -> Path:
    """
    # Returns the absolute path to a raw data file in the data/raw directory."""
    return RAW_DATA_DIR / filename

def get_project_root() -> Path:
    """
    # Returns the absolute path to the root 'data_engineering_project' folder."""
    return PROJECT_ROOT

# def get_logs_path(filename: str) -> Path:
#     """
#     # Returns the absolute path to a log file in the data/logs directory."""
#     LOG_DIR.mkdir(parents=True, exist_ok=True)
#     return LOG_DIR / filename


def get_config_path()-> Path:
    """Returns absolute path to configs/db_config.json"""
    return get_project_root() / "configs" / "db_config.json"
