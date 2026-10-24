{{ config(
    materialized='table',
    file_format='delta'
) }}

WITH product_order_month AS (
    SELECT
        order_items.product_key,
        TRUNC(date_dim.date, 'MONTH') AS month,
        order_items.order_id,
        SUM(order_items.price) AS order_revenue,
        COUNT(*) AS item_count,
        MAX(orders.review_score) AS review_score
    FROM {{ ref('fact_order_items') }} AS order_items
    INNER JOIN {{ ref('dim_date') }} AS date_dim
        ON order_items.order_date_key = date_dim.date_key
    LEFT JOIN {{ ref('fact_orders') }} AS orders
        ON order_items.order_id = orders.order_id
    GROUP BY
        order_items.product_key,
        TRUNC(date_dim.date, 'MONTH'),
        order_items.order_id
)

SELECT
    product_key,
    month,
    CAST(SUM(item_count) AS INT) AS units_sold,
    CAST(COUNT(*) AS INT) AS orders,
    SUM(order_revenue) AS revenue,
    SUM(order_revenue) / SUM(item_count) AS average_price,
    AVG(review_score) AS average_review_score
FROM product_order_month
GROUP BY product_key, month
