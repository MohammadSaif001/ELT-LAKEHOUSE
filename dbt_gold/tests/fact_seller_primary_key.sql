SELECT
    seller_key,
    month
FROM {{ ref('fact_seller') }}
GROUP BY seller_key, month
HAVING seller_key IS NULL
    OR month IS NULL
    OR COUNT(*) > 1
