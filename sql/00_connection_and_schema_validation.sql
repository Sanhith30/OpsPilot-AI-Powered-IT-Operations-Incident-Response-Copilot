-- Run in pgAdmin Query Tool or psql.
-- Database: opspilot
-- Read-only validation.
SELECT current_database(), current_user;
SELECT schema_name FROM information_schema.schemata WHERE schema_name='core';
SELECT COUNT(*) AS core_table_count FROM information_schema.tables WHERE table_schema='core' AND table_type='BASE TABLE';
SELECT table_name FROM information_schema.tables WHERE table_schema='core' AND table_type='BASE TABLE' ORDER BY table_name;
SELECT COUNT(*) AS foreign_key_count FROM information_schema.table_constraints WHERE constraint_schema='core' AND constraint_type='FOREIGN KEY';
