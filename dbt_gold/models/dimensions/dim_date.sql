{{ config(
    materialized='table',
    file_format='delta'
) }}

WITH calendar AS (
    SELECT EXPLODE(
        SEQUENCE(DATE '2025-01-01', DATE '2027-12-31', INTERVAL 1 DAY)
    ) AS date
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
