import logging
import logging.config
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from typing import Any

import yaml

from src.elt_lakehouse.spark.common.paths import PROJECT_ROOT

_CONFIG_LOADED = False


def _setup_logging() -> None:
    """
    ## Sets Up Logging Configuration
    - Sets up logging configuration from a YAML file.
    - This function is called once to configure the logging settings for the application.
    - It reads the logging configuration from 'config/logging_config.yaml' and applies it using the logging.config.dictConfig method.
    """
    global _CONFIG_LOADED

    if _CONFIG_LOADED:
        return

    config_path = PROJECT_ROOT / "config" / "logging_config.yaml"

    if not config_path.is_file():
        raise FileNotFoundError(f"Logging configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    file_handler = config.get("handlers", {}).get("file")

    if file_handler and "filename" in file_handler:
        log_path = Path(file_handler["filename"])

        if not log_path.is_absolute():
            log_path = PROJECT_ROOT / log_path

        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler["filename"] = str(log_path)

    logging.config.dictConfig(config)

    _CONFIG_LOADED = True


def get_logger(name: str) -> logging.Logger:
    """
    ### Gets a logger instance with the specified name.
    """
    _setup_logging()
    return logging.getLogger(name)


def kv(**fields: Any) -> str:
    """Format keyword arguments as logfmt: key=value key2=value2."""
    parts = []
    for key, value in fields.items():
        if value is None:
            parts.append(f"{key}=")
            continue
        text = str(value)
        if " " in text:
            text = f'"{text}"'
        parts.append(f"{key}={text}")
    return " ".join(parts)


@contextmanager
def log_duration(logger: logging.Logger, action: str, **context: Any) -> Iterator[None]:
    """
    Logs one "started" line and one "completed"/"failed" line around a
    block, with a consistent duration_s field. Re-raises on failure;
    never swallows an exception.
    """
    extra = f" {kv(**context)}" if context else ""
    logger.info("%s started%s", action, extra)
    start = perf_counter()
    try:
        yield
    except Exception:
        duration = perf_counter() - start
        logger.exception(
            "%s failed %s", action, kv(duration_s=round(duration, 2), **context)
        )
        raise
    else:
        duration = perf_counter() - start
        logger.info(
            "%s completed %s", action, kv(duration_s=round(duration, 2), **context)
        )
