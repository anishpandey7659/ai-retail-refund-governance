-- 1. Create a separate database for Keycloak.
-- The retail_refund database is created automatically
-- from POSTGRES_DB in your Docker Compose configuration.

CREATE DATABASE returnguard;

-- 2. Connect to Keycloak's database.
\connect returnguard

-- 3. Keep Keycloak's tables in their own schema.
CREATE SCHEMA IF NOT EXISTS keycloak;