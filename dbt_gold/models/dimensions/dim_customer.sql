{{ config(
    materialized='table',
    file_format='delta'
) }}

SELECT
    xxhash64(CAST(customer_id AS STRING)) AS customer_key,
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
FROM {{ source('silver', 'customers_silver') }}
