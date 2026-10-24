WITH counts AS (
    SELECT
        (SELECT COUNT(*) FROM {{ ref('fact_orders') }}) AS gold_count,
        (SELECT COUNT(*) FROM {{ source('silver', 'orders_silver') }}) AS silver_count
)
SELECT *
FROM counts
WHERE gold_count <> silver_count
