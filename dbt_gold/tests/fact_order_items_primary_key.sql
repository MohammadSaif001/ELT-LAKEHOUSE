SELECT
    order_id,
    order_item_id
FROM {{ ref('fact_order_items') }}
GROUP BY order_id, order_item_id
HAVING order_id IS NULL
    OR order_item_id IS NULL
    OR COUNT(*) > 1
