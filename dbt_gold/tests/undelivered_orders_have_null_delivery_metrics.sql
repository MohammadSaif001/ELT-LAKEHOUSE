SELECT
    orders.order_id,
    facts.delivery_days,
    facts.delivery_delay_days,
    facts.is_late,
    facts.delivered_date_key
FROM {{ ref('fact_orders') }} AS facts
INNER JOIN {{ source('silver', 'orders_silver') }} AS orders
    ON facts.order_id = orders.order_id
WHERE orders.order_delivered_customer_date IS NULL
    AND (
        facts.delivery_days IS NOT NULL
        OR facts.delivery_delay_days IS NOT NULL
        OR facts.is_late IS NOT NULL
        OR facts.delivered_date_key IS NOT NULL
    )
