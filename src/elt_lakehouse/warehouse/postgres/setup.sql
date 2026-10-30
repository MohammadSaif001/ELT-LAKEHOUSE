-- ELT Lakehouse Postgres Warehouse Setup Script
-- This script creates the roles and gold schema required by the ELT Lakehouse.

-- Create the roles used by the ELT Lakehouse.
-- The gold_owner role owns the gold schema and has full privileges
-- to manage the schema and its objects.
CREATE ROLE gold_owner
    NOLOGIN;

-- JDBC connection role used to load data into the gold schema.
CREATE ROLE gold_loader
    LOGIN
    PASSWORD 'Load3rP@ssw0rd';

-- Analyst role with read-only access to the gold schema.
CREATE ROLE gold_reader
    LOGIN
    PASSWORD 'R3ad0nlyP@ssw0rd';

-- Grant database connection access to the loader and reader roles.
GRANT CONNECT ON DATABASE elt_lakehouse
    TO gold_loader, gold_reader;

-- Create the gold schema and assign ownership to gold_owner.
CREATE SCHEMA gold AUTHORIZATION gold_owner;

-- Grant the loader permission to use and create objects in the gold schema.
GRANT USAGE, CREATE ON SCHEMA gold
    TO gold_loader;

-- The loader must be able to see, truncate, and refill the pre-created tables.
-- This also repairs privileges when setup.sql is rerun after table creation.
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA gold
    TO gold_loader;

-- Grant the reader permission to use the gold schema.
GRANT USAGE ON SCHEMA gold
    TO gold_reader;

-- Grant SELECT permission on all existing tables in the gold schema
-- to gold_reader.
GRANT SELECT ON ALL TABLES IN SCHEMA gold
    TO gold_reader;

-- Grant SELECT permission on future tables created by gold_loader
-- in the gold schema.
ALTER DEFAULT PRIVILEGES FOR ROLE gold_loader
    IN SCHEMA gold
    GRANT SELECT ON TABLES TO gold_reader;
