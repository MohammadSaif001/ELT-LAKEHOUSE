WITH date_bounds AS (
    SELECT
        MIN(date) AS first_date,
        MAX(date) AS last_date,
        COUNT(*) AS date_count
    FROM {{ ref('dim_date') }}
)
SELECT *
FROM date_bounds
WHERE date_count <> DATEDIFF(last_date, first_date) + 1
