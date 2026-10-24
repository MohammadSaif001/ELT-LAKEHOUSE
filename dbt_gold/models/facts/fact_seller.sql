{{ config(
    materialized='table',
    file_format='delta'
) }}

WITH seller_order_month AS (
    SELECT
        order_items.seller_key,
        TRUNC(date_dim.date, 'MONTH') AS month,
        order_items.order_id,
        SUM(order_items.price) AS order_revenue,
        COUNT(*) AS items_sold,
        MAX(orders.is_late) AS is_late,
        MAX(orders.delivery_days) AS delivery_days,
        MAX(orders.review_score) AS review_score
    FROM {{ ref('fact_order_items') }} AS order_items
    INNER JOIN {{ ref('dim_date') }} AS date_dim
        ON order_items.order_date_key = date_dim.date_key
    LEFT JOIN {{ ref('fact_orders') }} AS orders
        ON order_items.order_id = orders.order_id
    GROUP BY
        order_items.seller_key,
        TRUNC(date_dim.date, 'MONTH'),
        order_items.order_id
)

SELECT
    seller_key,
    month,
    SUM(order_revenue) AS revenue,
    CAST(COUNT(*) AS INT) AS orders,
    CAST(SUM(items_sold) AS INT) AS items_sold,
    AVG(CASE WHEN is_late IS NOT NULL THEN is_late END) AS late_rate,
    AVG(delivery_days) AS average_delivery_days,
    AVG(review_score) AS average_review_score
FROM seller_order_month
GROUP BY seller_key, month

