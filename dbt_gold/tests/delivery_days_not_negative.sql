SELECT order_id, delivery_days
FROM {{ ref('fact_orders') }}
WHERE delivery_days < 0