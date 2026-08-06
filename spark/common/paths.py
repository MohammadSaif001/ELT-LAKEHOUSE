from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# -------------------------
# Data
# -------------------------
DATA_DIR = PROJECT_ROOT / "data"
PROFILING_DIR = DATA_DIR / "profiling"
PROFILES_DIR = DATA_DIR / "dir"
RAW_DATA_DIR = DATA_DIR / "raw"

# -------------------------
# Metadata
# -------------------------

METADATA_DIR = PROJECT_ROOT / "metadata"
POOLS_DIR = METADATA_DIR / "pools"


# -------------------------
# Config
# -------------------------

CONFIG_DIR = PROJECT_ROOT / "config"

# -------------------------
# Generated
# -------------------------
GENERATED_DIR = PROJECT_ROOT / "storage" / "generated"