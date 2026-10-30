-- Primary keys already index the surrogate keys and the (entity, month) facts.
-- These cover the joins and filters analysts use most. Run after create_tables.sql.
CREATE INDEX IF NOT EXISTS ix_fact_order_items_order_id     ON gold.fact_order_items (order_id);
CREATE INDEX IF NOT EXISTS ix_fact_order_items_product_key  ON gold.fact_order_items (product_key);
CREATE INDEX IF NOT EXISTS ix_fact_order_items_seller_key   ON gold.fact_order_items (seller_key);
CREATE INDEX IF NOT EXISTS ix_fact_order_items_customer_key ON gold.fact_order_items (customer_key);
CREATE INDEX IF NOT EXISTS ix_fact_order_items_date_key     ON gold.fact_order_items (order_date_key);

CREATE INDEX IF NOT EXISTS ix_fact_orders_customer_key      ON gold.fact_orders (customer_key);
CREATE INDEX IF NOT EXISTS ix_fact_orders_purchase_date_key ON gold.fact_orders (purchase_date_key);
CREATE INDEX IF NOT EXISTS ix_fact_orders_status            ON gold.fact_orders (order_status);

CREATE INDEX IF NOT EXISTS ix_dim_customer_zip ON gold.dim_customer (customer_zip_code_prefix);
CREATE INDEX IF NOT EXISTS ix_dim_seller_zip   ON gold.dim_seller (seller_zip_code_prefix);
CREATE INDEX IF NOT EXISTS ix_dim_product_cat  ON gold.dim_product (product_category_name);
