{{ config(
    materialized='table',
    file_format='delta'
) }}

SELECT
    xxhash64(CAST(seller_id AS STRING)) AS seller_key,
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
FROM {{ source('silver', 'sellers_silver') }}
