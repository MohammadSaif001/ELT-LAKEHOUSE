from pathlib import Path

import pytest

from src.elt_lakehouse.ingestion.core.writer import write_delta
from src.elt_lakehouse.spark.common.spark_session import create_spark_session
from src.elt_lakehouse.spark.jobs import silver_job


@pytest.fixture(scope="module")
def spark():
    session = create_spark_session("silver-integration-test")
    yield session
    session.stop()


def test_bronze_to_silver_writes_outputs_and_quarantines_invalid_relationships(
    spark, tmp_path, monkeypatch
):
    bronze_dir = tmp_path / "bronze"
    silver_dir = tmp_path / "silver"
    bronze_dir.mkdir()
    silver_dir.mkdir()

    datasets = {
        "customers": [
            {
                "customer_id": "customer-1",
                "customer_unique_id": "unique-1",
                "customer_zip_code_prefix": "01001",
                "customer_city": "Sao Paulo",
                "customer_state": "SP",
            },
            {
                "customer_id": "customer-1",
                "customer_unique_id": "unique-1",
                "customer_zip_code_prefix": "01001",
                "customer_city": "Sao Paulo",
                "customer_state": "SP",
            },
        ],
        "geolocation": [
            {
                "geolocation_zip_code_prefix": 1001,
                "geolocation_lat": -23.55,
                "geolocation_lng": -46.63,
                "geolocation_city": "Sao Paulo",
                "geolocation_state": "SP",
            },
            {
                "geolocation_zip_code_prefix": 1001,
                "geolocation_lat": -23.56,
                "geolocation_lng": -46.64,
                "geolocation_city": "Sao Paulo",
                "geolocation_state": "SP",
            },
        ],
        "orders": [
            {
                "order_id": "order-1",
                "customer_id": "customer-1",
                "order_status": "delivered",
                "order_purchase_timestamp": "2024-01-01T10:00:00",
                "order_approved_at": "2024-01-01T10:05:00",
                "order_delivered_carrier_date": "2024-01-02T10:00:00",
                "order_delivered_customer_date": "2024-01-05T10:00:00",
                "order_estimated_delivery_date": "2024-01-10T10:00:00",
            },
            {
                "order_id": "order-1",
                "customer_id": "customer-1",
                "order_status": "delivered",
                "order_purchase_timestamp": "2024-01-01T10:00:00",
                "order_approved_at": "2024-01-01T10:05:00",
                "order_delivered_carrier_date": "2024-01-02T10:00:00",
                "order_delivered_customer_date": "2024-01-05T10:00:00",
                "order_estimated_delivery_date": "2024-01-10T10:00:00",
            },
            {
                "order_id": "order-invalid-customer",
                "customer_id": "customer-missing",
                "order_status": "created",
                "order_purchase_timestamp": "2024-01-02T10:00:00",
                "order_approved_at": "2024-01-02T10:05:00",
                "order_delivered_carrier_date": "2024-01-03T10:00:00",
                "order_delivered_customer_date": "2024-01-06T10:00:00",
                "order_estimated_delivery_date": "2024-01-11T10:00:00",
            },
        ],
        "order_items": [
            {
                "order_id": "order-1",
                "order_item_id": 1,
                "product_id": "product-1",
                "seller_id": "seller-1",
                "shipping_limit_date": "2024-01-03T10:00:00",
                "price": 10.5,
                "freight_value": 2.0,
            },
            {
                "order_id": "order-missing",
                "order_item_id": 1,
                "product_id": "product-1",
                "seller_id": "seller-1",
                "shipping_limit_date": "2024-01-03T10:00:00",
                "price": 11.5,
                "freight_value": 2.5,
            },
            {
                "order_id": "order-1",
                "order_item_id": 2,
                "product_id": "product-missing",
                "seller_id": "seller-1",
                "shipping_limit_date": "2024-01-03T10:00:00",
                "price": 12.5,
                "freight_value": 2.5,
            },
            {
                "order_id": "order-1",
                "order_item_id": 3,
                "product_id": "product-1",
                "seller_id": "seller-missing",
                "shipping_limit_date": "2024-01-03T10:00:00",
                "price": 13.5,
                "freight_value": 2.5,
            },
        ],
        "payments": [
            {
                "order_id": "order-1",
                "payment_sequential": 1,
                "payment_type": "credit_card",
                "payment_installments": 1,
                "payment_value": 12.5,
            },
            {
                "order_id": "order-missing",
                "payment_sequential": 1,
                "payment_type": "credit_card",
                "payment_installments": 1,
                "payment_value": 12.5,
            },
        ],
        "reviews": [
            {
                "review_id": "review-1",
                "order_id": "order-1",
                "review_score": 5,
                "review_comment_title": "",
                "review_comment_message": "",
                "review_creation_date": "2024-01-04T10:00:00",
            },
            {
                "review_id": "review-invalid-order",
                "order_id": "order-missing",
                "review_score": 1,
                "review_comment_title": "",
                "review_comment_message": "",
                "review_creation_date": "2024-01-04T10:00:00",
            },
        ],
        "products": [
            {
                "product_id": "product-1",
                "product_category_name": "books",
                "product_name_length": 5,
                "product_description_length": 20,
                "product_photo_quantity": 1,
                "product_weight_g": 100,
                "product_length_cm": 10,
                "product_height_cm": 2,
                "product_width_cm": 5,
            }
        ],
        "sellers": [
            {
                "seller_id": "seller-1",
                "seller_zip_code_prefix": "01001",
                "seller_city": "Sao Paulo",
                "seller_state": "SP",
            }
        ],
    }

    bronze_paths = {}
    for entity, rows in datasets.items():
        path = bronze_dir / f"{entity}_delta"
        write_delta(spark.createDataFrame(rows), str(path))
        bronze_paths[f"{entity}_delta"] = path

    output_paths = {}

    def read_test_delta(session, input_path):
        return session.read.format("delta").load(
            str(bronze_paths[Path(input_path).name])
        )

    def write_test_delta(df, output_path, mode="overwrite"):
        relative_path = Path(output_path).relative_to(silver_job.SILVER_DIR)
        destination = silver_dir / relative_path
        write_delta(df, str(destination), mode=mode)
        output_paths[str(relative_path)] = destination

    monkeypatch.setattr(silver_job, "create_spark_session", lambda: spark)
    monkeypatch.setattr(silver_job, "write_delta", write_test_delta)
    monkeypatch.setattr(
        "src.elt_lakehouse.spark.utils.validations.read_delta", read_test_delta
    )
    monkeypatch.setattr(
        "src.elt_lakehouse.spark.utils.validations.write_delta", write_test_delta
    )

    monkeypatch.setattr(spark, "stop", lambda: None)
    silver_job.run_silver_processing()

    expected_output_counts = {
        "customers_silver": 1,
        "geolocation_silver": 2,
        "orders_silver": 1,
        "order_items_silver": 1,
        "payments_silver": 1,
        "reviews_silver": 1,
        "products_silver": 1,
        "sellers_silver": 1,
        "quarantine/orders_missing_customer": 1,
        "quarantine/order_items_missing_order": 1,
        "quarantine/order_items_missing_product": 1,
        "quarantine/order_items_missing_seller": 1,
        "quarantine/payments_missing_order": 1,
        "quarantine/reviews_missing_order": 1,
    }
    assert set(output_paths) == set(expected_output_counts)

    for output_name, expected_count in expected_output_counts.items():
        actual_count = (
            spark.read.format("delta").load(str(output_paths[output_name])).count()
        )
        assert actual_count == expected_count, output_name
