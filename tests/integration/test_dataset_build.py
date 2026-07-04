import json
from generators.build_dataset import main

#========================
# Test the build pipeline
#========================
def test_build_pipeline(tmp_path):

    main(output_dir=tmp_path)
    expected_files = [
        "generated_orders_data.json",
        "generated_order_items_data.json",
        "generated_payments_data.json",
        "generated_reviews_data.json",
    ]
    # File creation check
    for filename in expected_files:
        file_path = tmp_path / filename
        assert file_path.exists(), (
            f"{filename} was not created"
        )
    # Content validation
    with open(
        tmp_path / "generated_orders_data.json"
    ) as f:
        orders = json.load(f)
    assert isinstance(orders,list)
    assert len(orders) > 0
    assert "order_id" in orders[0]
