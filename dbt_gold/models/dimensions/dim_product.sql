{{ config(
    materialized='table',
    file_format='delta'
) }}

SELECT
    xxhash64(CAST(product_id AS STRING)) AS product_key,
    product_id,
    product_category_name,
    product_name_length,
    product_description_length,
    product_photo_quantity,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm
FROM {{ source('silver', 'products_silver') }}
