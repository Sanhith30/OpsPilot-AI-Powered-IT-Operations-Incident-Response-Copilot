# PostgreSQL Global Connection Pool and PgBouncer Sizing Guide

## Overview
This operational guide defines connection pool configurations, PgBouncer architectures, and capacity planning for all PostgreSQL database clusters in OpsPilot.

## Symptoms of Connection Pool Saturation
- Database error: `FATAL: remaining connection slots are reserved for non-replication superuser connections`
- Error: `FATAL: sorry, too many clients already`
- Microservices experiencing sudden spikes in connection acquisition latency
- Connection starvation propagating across multiple services sharing the same database instance

## Diagnostic Procedures
1. Query active client connections grouped by database and application:
   ```sql
   SELECT datname, usename, application_name, state, count(*)
   FROM pg_stat_activity
   GROUP BY datname, usename, application_name, state
   ORDER BY count(*) DESC;
   ```
2. Identify queries stuck in `idle in transaction` state for over 60 seconds:
   ```sql
   SELECT pid, now() - state_change AS idle_duration, query
   FROM pg_stat_activity
   WHERE state = 'idle in transaction'
     AND now() - state_change > interval '60 seconds';
   ```
3. Inspect PgBouncer pool statistics via `SHOW POOLS;` and `SHOW STATS;` in the pgbouncer admin console.

## Sizing and Mitigation Rules
1. Never configure application microservice pools such that `sum(microservice_instances * max_pool_size) > pgbouncer_max_client_conn`.
2. For microservices with high concurrency, configure PgBouncer in `transaction` pooling mode rather than `session` mode.
3. Terminate stuck connection sessions holding idle locks using `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE ...;`.
4. Ensure `idle_in_transaction_session_timeout` is configured globally to 30000ms.

## Verification
1. Total active connections remain below 75% of server `max_connections`.
2. PgBouncer `cl_waiting` (clients waiting for server connections) metric returns to 0.
3. Database query latency stabilizes within expected SLAs.
