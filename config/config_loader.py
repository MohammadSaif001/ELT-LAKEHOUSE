import yaml
from pathlib import Path
from functools import lru_cache
from spark.common.logger import get_logger

logger = get_logger(__name__)

CONFIG_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=None)
def load_yaml(config_file: str) -> dict:
    """Load and cache a YAML configuration file."""
    config_path = CONFIG_DIR / config_file
    logger.info("Configuration directory set: path=%s", CONFIG_DIR)
    logger.info("Loading configuration: path=%s", config_path)

    if not config_path.is_file():
        logger.error("Configuration file not found: path=%s", config_path)
        raise FileNotFoundError(
            f"Configuration file '{config_file}' not found in '{CONFIG_DIR}'"
        )

    try:
        with config_path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file) or {}

        logger.info(
            "Configuration loaded successfully: path=%s, keys=%s",
            config_path,
            list(config.keys()),
        )
        return config

    except yaml.YAMLError:
        logger.exception("Invalid YAML configuration: path=%s", config_path)
        raise

