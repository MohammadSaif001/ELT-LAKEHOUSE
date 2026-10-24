{{ config(
    materialized='table',
    file_format='delta'
) }}

SELECT
    oi.order_id,
    oi.order_item_id,
    product.product_key,
    seller.seller_key,
    customer.customer_key,
    date_dim.date_key AS order_date_key,
    CAST(oi.shipping_limit_date AS TIMESTAMP) AS shipping_limit_date,
    oi.price,
    oi.freight_value
FROM {{ source('silver', 'order_items_silver') }} AS oi
LEFT JOIN {{ source('silver', 'orders_silver') }} AS orders
    ON oi.order_id = orders.order_id
LEFT JOIN {{ ref('dim_product') }} AS product
    ON oi.product_id = product.product_id
LEFT JOIN {{ ref('dim_seller') }} AS seller
    ON oi.seller_id = seller.seller_id
LEFT JOIN {{ ref('dim_customer') }} AS customer
    ON orders.customer_id = customer.customer_id
LEFT JOIN {{ ref('dim_date') }} AS date_dim
    ON CAST(orders.order_purchase_timestamp AS DATE) = date_dim.date
