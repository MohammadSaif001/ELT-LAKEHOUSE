SELECT
    orders.order_id,
    facts.delivery_days,
    facts.delivery_delay_days,
    facts.is_late
FROM {{ ref('fact_orders') }} AS facts
INNER JOIN {{ source('silver', 'orders_silver') }} AS orders
    ON facts.order_id = orders.order_id
WHERE orders.order_delivered_customer_date IS NOT NULL
    AND (
        facts.delivery_days IS NULL
        OR facts.delivery_delay_days IS NULL
        OR facts.is_late IS NULL
        OR facts.delivery_days <> DATEDIFF(
            CAST(orders.order_delivered_customer_date AS DATE),
            CAST(orders.order_purchase_timestamp AS DATE)
        )
        OR facts.delivery_delay_days <> DATEDIFF(
            CAST(orders.order_delivered_customer_date AS DATE),
            CAST(orders.order_estimated_delivery_date AS DATE)
        )
        OR facts.is_late <> CASE
            WHEN CAST(orders.order_delivered_customer_date AS DATE)
                > CAST(orders.order_estimated_delivery_date AS DATE) THEN 1
            ELSE 0
        END
    )
