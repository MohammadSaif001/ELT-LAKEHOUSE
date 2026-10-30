import logging
import logging.config
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from copy import copy
from pathlib import Path
from time import perf_counter
from typing import Any

import yaml

from src.elt_lakehouse.spark.common.paths import PROJECT_ROOT

_CONFIG_LOADED = False


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.INFO: "\x1b[32m",
        logging.WARNING: "\x1b[33m",
        logging.ERROR: "\x1b[31m",
        logging.CRITICAL: "\x1b[31m",
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno)
        if color is None or not sys.stderr.isatty():
            return super().format(record)

        colored_record = copy(record)
        colored_record.levelname = f"{color}{record.levelname}\x1b[0m"
        return super().format(colored_record)


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

    for handler in config.get("handlers", {}).values():
        if "filename" not in handler:
            continue

        log_path = Path(handler["filename"])

        if not log_path.is_absolute():
            log_path = PROJECT_ROOT / log_path

        log_path.parent.mkdir(parents=True, exist_ok=True)

        handler["filename"] = str(log_path)

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
