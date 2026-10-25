from functools import cache
from pathlib import Path

import yaml

from src.elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)

CONFIG_DIR = Path(__file__).resolve().parent

# Project root: ELT-lakehouse/
PROJECT_ROOT = Path(__file__).resolve().parents[4]


def display_path(path: Path) -> str:
    """Return a project-relative path for logging when possible."""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(path)

@cache
def load_yaml(config_file: str) -> dict:
    """Load and cache a YAML configuration file."""
    config_path = CONFIG_DIR / config_file
    logger.info("Configuration directory set: path=%s", display_path(CONFIG_DIR))
    logger.info("Loading configuration: path=%s", display_path(config_path))

    if not config_path.is_file():
        logger.error("Configuration file not found: path=%s", display_path(config_path))
        raise FileNotFoundError(
            f"Configuration file '{config_file}' not found in '{CONFIG_DIR}'"
        )

    try:
        with config_path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file) or {}

        logger.info(
            "Configuration loaded: file=%s, keys=%s",
            config_file,
            sorted(config),
        )
        return config

    except yaml.YAMLError:
        logger.exception("Invalid YAML configuration: path=%s", display_path(config_path))
        raise
