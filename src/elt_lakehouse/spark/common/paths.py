from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]

# ====================================
# Data
# ====================================
DATA_DIR = PROJECT_ROOT / "data"
PROFILING_DIR = DATA_DIR / "profiling"
PROFILES_DIR = DATA_DIR / "dir"
RAW_DATA_DIR = DATA_DIR / "raw"

# =============================
# Metadata
# =============================

METADATA_DIR = PROJECT_ROOT / "metadata"
POOLS_DIR = METADATA_DIR / "pools"


# =============================
# Config
# =============================

CONFIG_DIR = PROJECT_ROOT / "config"

# =============================
# Generated
# =============================
GENERATED_DIR = PROJECT_ROOT / "storage" / "generated"

# ====================================
# Delta Tables
# ====================================
STORAGE_DIR = PROJECT_ROOT / "storage"
BRONZE_DIR = STORAGE_DIR / "bronze"
SILVER_DIR = STORAGE_DIR / "silver"
GOLD_DIR = STORAGE_DIR / "gold"

# =============================
# Postgres Directories
# =============================
SRC_DIR = PROJECT_ROOT/"src"
ELT_LAKEHOUSE_DIR = SRC_DIR / "elt_lakehouse"
WAREHOUSE_DIR = ELT_LAKEHOUSE_DIR / "warehouse"
POSTGRES_DIR = WAREHOUSE_DIR / "postgres"

# =====================================
# Config Files
# =====================================
CONFIG_DIR = PROJECT_ROOT / "config"

# =====================================
# Contract Files
# =====================================
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
