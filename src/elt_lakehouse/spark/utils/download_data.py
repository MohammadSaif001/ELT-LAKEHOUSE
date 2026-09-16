import pathlib

import kaggle


def download_dataset(DATASET_ID ="olistbr/brazilian-ecommerce", 
                     DATASET_DOWNLOAD_PATH = "data/raw/olist"):
    """Download a dataset from Kaggle."""
    
    if not pathlib.Path(DATASET_DOWNLOAD_PATH).exists():
        pathlib.Path(DATASET_DOWNLOAD_PATH).mkdir(parents=True, exist_ok=True)
        print(f"Created directory '{DATASET_DOWNLOAD_PATH}' for dataset download.")
    
    try:
        kaggle.api.dataset_download_files(
            DATASET_ID, 
            path=DATASET_DOWNLOAD_PATH,
            unzip=True
        )
        print(f"Dataset '{DATASET_ID}' downloaded and extracted to '{DATASET_DOWNLOAD_PATH}'")
    except Exception as e:
        print(f"Error occurred while downloading dataset: {e}") 


download_dataset()