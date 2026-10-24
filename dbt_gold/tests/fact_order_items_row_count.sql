WITH counts AS (
    SELECT
        (SELECT COUNT(*) FROM {{ ref('fact_order_items') }}) AS gold_count,
        (SELECT COUNT(*) FROM {{ source('silver', 'order_items_silver') }}) AS silver_count
)
SELECT *
FROM counts
WHERE gold_count <> silver_count
