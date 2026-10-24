WITH revenue_totals AS (
    SELECT
        'fact_order_items' AS model_name,
        COALESCE(SUM(price), CAST(0 AS DOUBLE)) AS revenue
    FROM {{ ref('fact_order_items') }}

    UNION ALL

    SELECT 'fact_seller', COALESCE(SUM(revenue), CAST(0 AS DOUBLE))
    FROM {{ ref('fact_seller') }}

    UNION ALL

    SELECT 'fact_product', COALESCE(SUM(revenue), CAST(0 AS DOUBLE))
    FROM {{ ref('fact_product') }}
)
SELECT
    items.revenue AS item_revenue,
    sellers.revenue AS seller_revenue,
    products.revenue AS product_revenue
FROM revenue_totals AS items
CROSS JOIN revenue_totals AS sellers
CROSS JOIN revenue_totals AS products
WHERE items.model_name = 'fact_order_items'
    AND sellers.model_name = 'fact_seller'
    AND products.model_name = 'fact_product'
    AND (
        ABS(items.revenue - sellers.revenue) > 0.01
        OR ABS(items.revenue - products.revenue) > 0.01
    )
