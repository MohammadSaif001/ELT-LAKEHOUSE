{{ config(
    materialized='table',
    file_format='delta'
) }}

SELECT
    review_id,
    order_id,
    review_comment_title,
    review_comment_message
FROM {{ source('silver', 'reviews_silver') }}
