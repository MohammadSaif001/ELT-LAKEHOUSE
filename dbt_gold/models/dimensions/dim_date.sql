{{ config(
    materialized='table',
    file_format='delta'
) }}

WITH bounds AS (
    SELECT
        date_sub(MIN(CAST(order_purchase_timestamp AS DATE)), 30) AS start_date,
        date_add(MAX(CAST(order_estimated_delivery_date AS DATE)), 30) AS end_date
    FROM {{ source('silver', 'orders_silver') }}
),
calendar AS (
    SELECT EXPLODE(
        SEQUENCE(
            start_date,
            end_date,
            INTERVAL 1 DAY
        )
    ) AS date
    FROM bounds
)

SELECT
    CAST(DATE_FORMAT(date, 'yyyyMMdd') AS INT) AS date_key,
    date,
    YEAR(date) AS year,
    QUARTER(date) AS quarter,
    MONTH(date) AS month,
    DATE_FORMAT(date, 'MMMM') AS month_name,
    DAYOFMONTH(date) AS day,
    DAYOFWEEK(date) AS day_of_week,
    DATE_FORMAT(date, 'EEEE') AS day_name,
    DAYOFWEEK(date) IN (1, 7) AS is_weekend
FROM calendar
