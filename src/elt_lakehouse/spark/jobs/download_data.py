from pathlib import Path

import kaggle

from src.elt_lakehouse.spark.common.logger import get_logger
from src.elt_lakehouse.spark.common.paths import RAW_DATA_DIR

logger = get_logger(__name__)

DATASET_ID = "olistbr/brazilian-ecommerce"
DATASET_DOWNLOAD_PATH = RAW_DATA_DIR / "olist"
REQUIRED_DATA_FILES = (
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
)


def missing_dataset_files(dataset_path: Path = DATASET_DOWNLOAD_PATH) -> list[str]:
    """Return required dataset files that are missing from the local copy."""
    return [name for name in REQUIRED_DATA_FILES if not (dataset_path / name).is_file()]


def download_dataset(
    dataset_id: str = DATASET_ID,
    dataset_download_path: Path = DATASET_DOWNLOAD_PATH,
) -> Path:
    """Download and validate the Olist dataset, reusing a complete local copy."""
    dataset_download_path = Path(dataset_download_path)
    missing_files = missing_dataset_files(dataset_download_path)
    if not missing_files:
        logger.info("Dataset already exists at %s; skipping download.", dataset_download_path)
        return dataset_download_path

    dataset_download_path.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading Kaggle dataset %s to %s.", dataset_id, dataset_download_path)
    try:
        kaggle.api.dataset_download_files(
            dataset_id, path=str(dataset_download_path), unzip=True
        )
    except Exception as exc:
        logger.exception("operation failed; re-raising")
        raise RuntimeError(
            "Kaggle dataset download failed. Install the project dependencies and "
            "configure Kaggle API credentials, then retry."
        ) from exc

    missing_files = missing_dataset_files(dataset_download_path)
    if missing_files:
        raise RuntimeError(
            "Kaggle download completed, but required dataset files are missing: "
            + ", ".join(missing_files)
        )

    logger.info("Dataset downloaded and validated at %s.", dataset_download_path)
    return dataset_download_path


if __name__ == "__main__":
    download_dataset()
