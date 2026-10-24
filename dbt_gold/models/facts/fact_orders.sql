{{ config(
    materialized='table',
    file_format='delta'
) }}

WITH item_counts AS (
    SELECT
        order_id,
        COUNT(*) AS order_item_count
    FROM {{ source('silver', 'order_items_silver') }}
    GROUP BY order_id
),
payment_totals AS (
    SELECT
        order_id,
        SUM(payment_value) AS order_payment_value,
        MAX(payment_installments) AS max_installments
    FROM {{ source('silver', 'payments_silver') }}
    GROUP BY order_id
),
payment_type_totals AS (
    SELECT
        order_id,
        payment_type,
        SUM(payment_value) AS payment_type_value
    FROM {{ source('silver', 'payments_silver') }}
    GROUP BY order_id, payment_type
),
ranked_payment_types AS (
    SELECT
        order_id,
        payment_type,
        ROW_NUMBER() OVER (
            PARTITION BY order_id
            ORDER BY payment_type_value DESC, payment_type ASC
        ) AS payment_type_rank
    FROM payment_type_totals
),
latest_reviews AS (
    SELECT
        order_id,
        review_score,
        ROW_NUMBER() OVER (
            PARTITION BY order_id
            ORDER BY review_creation_date DESC, review_id DESC
        ) AS review_rank
    FROM {{ source('silver', 'reviews_silver') }}
)

SELECT
    orders.order_id,
    customer.customer_key,
    orders.order_status,
    purchase_date.date_key AS purchase_date_key,
    approved_date.date_key AS approved_date_key,
    carrier_date.date_key AS carrier_date_key,
    delivered_date.date_key AS delivered_date_key,
    estimated_date.date_key AS estimated_date_key,
    CAST(COALESCE(item_counts.order_item_count, 0) AS INT) AS order_item_count,
    payment_totals.order_payment_value,
    payment_totals.max_installments,
    ranked_payment_types.payment_type AS main_payment_type,
    latest_reviews.review_score,
    DATEDIFF(
        CAST(orders.order_delivered_customer_date AS DATE),
        CAST(orders.order_purchase_timestamp AS DATE)
    ) AS delivery_days,
    DATEDIFF(
        CAST(orders.order_delivered_customer_date AS DATE),
        CAST(orders.order_estimated_delivery_date AS DATE)
    ) AS delivery_delay_days,
    CASE
        WHEN orders.order_delivered_customer_date IS NULL THEN NULL
        WHEN CAST(orders.order_delivered_customer_date AS DATE)
            > CAST(orders.order_estimated_delivery_date AS DATE) THEN 1
        ELSE 0
    END AS is_late
FROM {{ source('silver', 'orders_silver') }} AS orders
LEFT JOIN {{ ref('dim_customer') }} AS customer
    ON orders.customer_id = customer.customer_id
LEFT JOIN item_counts
    ON orders.order_id = item_counts.order_id
LEFT JOIN payment_totals
    ON orders.order_id = payment_totals.order_id
LEFT JOIN ranked_payment_types
    ON orders.order_id = ranked_payment_types.order_id
    AND ranked_payment_types.payment_type_rank = 1
LEFT JOIN latest_reviews
    ON orders.order_id = latest_reviews.order_id
    AND latest_reviews.review_rank = 1
LEFT JOIN {{ ref('dim_date') }} AS purchase_date
    ON CAST(orders.order_purchase_timestamp AS DATE) = purchase_date.date
LEFT JOIN {{ ref('dim_date') }} AS approved_date
    ON CAST(orders.order_approved_at AS DATE) = approved_date.date
LEFT JOIN {{ ref('dim_date') }} AS carrier_date
    ON CAST(orders.order_delivered_carrier_date AS DATE) = carrier_date.date
LEFT JOIN {{ ref('dim_date') }} AS delivered_date
    ON CAST(orders.order_delivered_customer_date AS DATE) = delivered_date.date
LEFT JOIN {{ ref('dim_date') }} AS estimated_date
    ON CAST(orders.order_estimated_delivery_date AS DATE) = estimated_date.date
