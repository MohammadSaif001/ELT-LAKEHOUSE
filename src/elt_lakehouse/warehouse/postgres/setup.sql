-- ELT Lakehouse Postgres Warehouse Setup Script
-- This script creates the roles and gold schema required by the ELT Lakehouse.

-- Create the roles used by the ELT Lakehouse if they do not already exist.
-- The role passwords are only applied when a role is first created.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'gold_owner') THEN
        CREATE ROLE gold_owner NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'gold_loader') THEN
        CREATE ROLE gold_loader LOGIN PASSWORD 'Load3rP@ssw0rd';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'gold_reader') THEN
        CREATE ROLE gold_reader LOGIN PASSWORD 'R3ad0nlyP@ssw0rd';
    END IF;
END
$$;

-- Grant database connection access to the loader and reader roles.
GRANT CONNECT ON DATABASE elt_lakehouse
    TO gold_loader, gold_reader;

-- Create the gold schema and assign ownership to gold_owner.
CREATE SCHEMA IF NOT EXISTS gold AUTHORIZATION gold_owner;
ALTER SCHEMA gold OWNER TO gold_owner;

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
