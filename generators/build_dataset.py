"""
Main entry point for dataset generation.

This module coordinates the execution of dataset generators in the required
order, ensuring dependencies between datasets are respected. It generates
customers, geolocations, sellers, products, orders, order items, payments,
and reviews as part of a complete data generation workflow.
"""
from generators.customers.build_customers import build_customers
from generators.customers.build_geolocations import build_geolocations
from generators.sellers.build_sellers import build_sellers
from generators.products.build_products import build_products
from generators.orders.build_orders import build_orders, build_order_items
from generators.payments.build_payments import build_payments
from generators.reviews.build_reviews import build_reviews


def main(output_dir : str ="storage/generated") -> None:
    print("Starting generation...\n")
    build_customers(output_dir)
    print("Customers data generated successfully.")
    build_geolocations(output_dir)
    print("Geolocations data generated successfully.")
    build_sellers(output_dir)
    print("Sellers data generated successfully.")
    build_products(output_dir)
    print("Products data generated successfully.")
    build_orders(output_dir)
    print("Orders data generated successfully.")
    build_order_items(output_dir)
    print("Order items data generated successfully.")
    build_payments(output_dir)
    print("Payments data generated successfully.")
    build_reviews(output_dir)
    print("Reviews data generated successfully.\n")
    print("Generation completed successfully!")


if __name__ == "__main__":
    main()