{{ config(
    materialized='table',
    file_format='delta'
) }}

WITH location_coordinates AS (
    SELECT
        LPAD(CAST(geolocation_zip_code_prefix AS STRING), 5, '0') AS zip_code_prefix,
        AVG(geolocation_lat) AS geolocation_lat,
        AVG(geolocation_lng) AS geolocation_lng
    FROM {{ source('silver', 'geolocation_silver') }}
    GROUP BY LPAD(CAST(geolocation_zip_code_prefix AS STRING), 5, '0')
),
city_state_counts AS (
    SELECT
        LPAD(CAST(geolocation_zip_code_prefix AS STRING), 5, '0') AS zip_code_prefix,
        geolocation_city,
        geolocation_state,
        COUNT(*) AS row_count,
        ROW_NUMBER() OVER (
            PARTITION BY LPAD(CAST(geolocation_zip_code_prefix AS STRING), 5, '0')
            ORDER BY COUNT(*) DESC, geolocation_city ASC, geolocation_state ASC
        ) AS location_rank
    FROM {{ source('silver', 'geolocation_silver') }}
    GROUP BY
        LPAD(CAST(geolocation_zip_code_prefix AS STRING), 5, '0'),
        geolocation_city,
        geolocation_state
)

SELECT
    coordinates.zip_code_prefix,
    coordinates.geolocation_lat,
    coordinates.geolocation_lng,
    city_state.geolocation_city,
    city_state.geolocation_state
FROM location_coordinates AS coordinates
INNER JOIN city_state_counts AS city_state
    ON coordinates.zip_code_prefix = city_state.zip_code_prefix
    AND city_state.location_rank = 1
