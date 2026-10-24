SELECT
    product_key,
    month
FROM {{ ref('fact_product') }}
GROUP BY product_key, month
HAVING product_key IS NULL
    OR month IS NULL
    OR COUNT(*) > 1
