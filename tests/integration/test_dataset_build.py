from src.elt_lakehouse.generators.base.data_loading import load_generated_data
from src.elt_lakehouse.spark.jobs.dataset_job import run_dataset_job


# ========================
# Test the build pipeline
# ========================
def test_build_pipeline(tmp_path):

    run_dataset_job(output_dir=tmp_path)
    expected_files = [
        "generated_orders_data.parquet",
        "generated_order_items_data.parquet",
        "generated_payments_data.parquet",
        "generated_reviews_data.parquet",
    ]
    # File creation check
    for filename in expected_files:
        file_path = tmp_path / filename
        assert file_path.exists(), f"{filename} was not created"
    # Content validation
    orders = load_generated_data("generated_orders_data.parquet", base_dir=tmp_path)
    assert isinstance(orders, list)
    assert len(orders) > 0
    assert "order_id" in orders[0]
