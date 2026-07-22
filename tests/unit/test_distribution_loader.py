from generators.base.distribution_loader import load_distribution


def test_order_status_distribution() -> None:

    dist = load_distribution("order_status_distribution.json")

    assert len(dist) > 0