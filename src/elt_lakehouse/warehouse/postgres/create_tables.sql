-- Gold tables. Spark TRUNCATEs and refills these, so keys and indexes survive.
-- No FOREIGN KEY constraints on purpose: TRUNCATE fails on a referenced table, and the
-- dbt relationships tests already verify every fact key exists in its dimension.
--
-- Column lists mirror dbt_gold/models (tests/unit/test_postgres_ddl.py checks this).
-- Types are deliberately wide so they accept what Spark writes:
--   Silver "integer" columns -> BIGINT, "number" columns -> DOUBLE PRECISION,
--   explicit CAST(... AS INT) in dbt -> INTEGER, xxhash64 keys -> BIGINT.
-- Run order: create_schema.sql, create_tables.sql, create_indexes.sql, grants.sql.

-- ---------------------------------------------------------------- dimensions

CREATE TABLE IF NOT EXISTS gold.dim_date (
    date_key     INTEGER PRIMARY KEY,          -- yyyymmdd
    date         DATE NOT NULL UNIQUE,
    year         INTEGER,
    quarter      INTEGER,
    month        INTEGER,
    month_name   TEXT,
    day          INTEGER,
    day_of_week  INTEGER,                      -- Spark dayofweek: 1 = Sunday
    day_name     TEXT,
    is_weekend   BOOLEAN
);

CREATE TABLE IF NOT EXISTS gold.dim_customer (
    customer_key             BIGINT PRIMARY KEY,
    customer_id              TEXT NOT NULL UNIQUE,
    customer_unique_id       TEXT,
    customer_zip_code_prefix TEXT,
    customer_city            TEXT,
    customer_state           TEXT
);

CREATE TABLE IF NOT EXISTS gold.dim_seller (
    seller_key             BIGINT PRIMARY KEY,
    seller_id              TEXT NOT NULL UNIQUE,
    seller_zip_code_prefix TEXT,
    seller_city            TEXT,
    seller_state           TEXT
);

CREATE TABLE IF NOT EXISTS gold.dim_product (
    product_key                BIGINT PRIMARY KEY,
    product_id                 TEXT NOT NULL UNIQUE,
    product_category_name      TEXT,
    product_name_length        BIGINT,
    product_description_length BIGINT,
    product_photo_quantity     BIGINT,
    product_weight_g           BIGINT,
    product_length_cm          BIGINT,
    product_height_cm          BIGINT,
    product_width_cm           BIGINT
);

CREATE TABLE IF NOT EXISTS gold.dim_location (
    zip_code_prefix   TEXT PRIMARY KEY,        -- string: keeps leading zeros
    geolocation_lat   DOUBLE PRECISION,
    geolocation_lng   DOUBLE PRECISION,
    geolocation_city  TEXT,
    geolocation_state TEXT
);

-- --------------------------------------------------------------------- facts

-- Grain: one row per order item.
CREATE TABLE IF NOT EXISTS gold.fact_order_items (
    order_id            TEXT NOT NULL,
    order_item_id       BIGINT NOT NULL,
    product_key         BIGINT,
    seller_key          BIGINT,
    customer_key        BIGINT,
    order_date_key      INTEGER,
    shipping_limit_date TIMESTAMP,
    price               DOUBLE PRECISION,
    freight_value       DOUBLE PRECISION,
    PRIMARY KEY (order_id, order_item_id)
);

-- Grain: one row per order.
CREATE TABLE IF NOT EXISTS gold.fact_orders (
    order_id             TEXT PRIMARY KEY,
    customer_key         BIGINT,
    order_status         TEXT,
    purchase_date_key    INTEGER,
    approved_date_key    INTEGER,
    carrier_date_key     INTEGER,
    delivered_date_key   INTEGER,
    estimated_date_key   INTEGER,
    order_item_count     INTEGER,
    order_payment_value  DOUBLE PRECISION,
    max_installments     BIGINT,
    main_payment_type    TEXT,
    review_score         BIGINT,
    delivery_days        INTEGER,
    delivery_delay_days  INTEGER,
    is_late              INTEGER               -- 1 late, 0 on time, NULL undelivered
);

-- Grain: one row per seller per purchase month.
CREATE TABLE IF NOT EXISTS gold.fact_seller (
    seller_key            BIGINT NOT NULL,
    month                 DATE NOT NULL,       -- first day of the month
    revenue               DOUBLE PRECISION,
    orders                INTEGER,
    items_sold            INTEGER,
    average_is_late       DOUBLE PRECISION,
    average_delivery_days DOUBLE PRECISION,
    average_review_score  DOUBLE PRECISION,
    PRIMARY KEY (seller_key, month)
);

-- Grain: one row per product per purchase month.
CREATE TABLE IF NOT EXISTS gold.fact_product (
    product_key          BIGINT NOT NULL,
    month                DATE NOT NULL,
    units_sold           INTEGER,
    orders               INTEGER,
    revenue              DOUBLE PRECISION,
    average_price        DOUBLE PRECISION,
    average_review_score DOUBLE PRECISION,
    PRIMARY KEY (product_key, month)
);
