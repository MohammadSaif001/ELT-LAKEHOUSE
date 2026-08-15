from collections import Counter
from src.elt_lakehouse.generators.base.distribution_loader import load_distribution
from src.elt_lakehouse.generators.base.data_loading import load_generated_data

# Helpler function to calculate the distribution of values in a given column of a list of dictionaries.

def calculate_distribution(rows, column)-> dict[str,float]:

    counts:Counter = Counter(
        row[column]
        for row in rows
    )

    total:int = len(rows)

    return {
        str(key): value / total
        for key, value in counts.items()
    }

def test_order_status_distribution()-> None:

    historical = load_distribution("order_status_distribution.json")
    orders = load_generated_data("generated_orders_data.json")
    generated = calculate_distribution(orders, "order_status")

    for status in historical:

        assert abs(
            generated.get(status, 0)
            -
            historical[status]
        ) < 0.05,(
            f"Distribution mismatch for {status}: "
            f"generated={generated.get(status,0):.3f}, "
            f"historical={historical[status]:.3f}"
        )

def test_payment_type_distribution():
    historical = load_distribution(
        "payment_type_distribution.json"
    )
    payments = load_generated_data(
        "generated_payments_data.json"
    )
    generated = calculate_distribution(payments, "payment_type")
    for payment_type in historical:
        assert abs(
            generated.get(payment_type, 0)
            -
            historical[payment_type]
        ) < 0.05, (
            f"Distribution mismatch for {payment_type}: "
            f"generated={generated.get(payment_type,0):.3f}, "
            f"historical={historical[payment_type]:.3f}"
        )

def test_product_category_distribution():
    historical = load_distribution(
        "product_category_distribution.json"
    )
    products = load_generated_data(
        "generated_products_data.json"
        )
    generated = calculate_distribution(products, "product_category_name")
    
    for category in historical:
        assert abs(
            generated.get(category, 0)
            -
            historical[category]
        ) < 0.05, (
            f"Distribution mismatch for {category}: "
            f"generated={generated.get(category,0):.3f}, "
            f"historical={historical[category]:.3f}"
        )
        
def test_review_score_distribution():
    historical = load_distribution(
        "review_score_distribution.json"
    )
    reviews = load_generated_data(
        "generated_reviews_data.json"
    )
    generated = calculate_distribution(reviews, "review_score")
    
    for score in historical:
        assert abs(
            generated.get(score, 0)
            -
            historical[score]
        ) < 0.05, (
            f"Distribution mismatch for {score}: "
            f"generated={generated.get(score,0):.3f}, "
            f"historical={historical[score]:.3f}"
        )
