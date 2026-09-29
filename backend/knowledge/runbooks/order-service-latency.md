# Order Service Checkout Latency and Database Deadlock Runbook

## Symptoms
The Order Service experiences elevated latency on checkout transactions and returns HTTP 504 Gateway Timeouts on `POST /v1/orders`.
Common symptoms include:
- Checkout transaction latency p99 exceeding 8000ms
- Database deadlock exceptions (`DeadlockDetected: deadlock detected in order_items table`)
- Thread pool starvation on order-service worker pods
- Pending orders backing up in checkout submission queues

## Investigation
1. Inspect order-service logs for database deadlock and transaction lock wait errors.
2. Query `pg_stat_activity` on the order database to identify conflicting locks on `orders` and `order_items` tables.
3. Review inventory reservation RPC latency to determine whether downstream dependency delays are holding database locks open.
4. Check recent deployments to order-service to identify code changes in order placement transactions.

## Mitigation
1. Terminate long-waiting or blocked backend transactions using `pg_terminate_backend(pid)`.
2. Temporarily enable asynchronous order submission queuing to decouple checkout requests from immediate database persistence.
3. If recent deployment introduced a lock ordering regression, execute immediate deployment rollback.

## Verification
1. Verify order creation throughput returns to normal operating baseline.
2. Confirm database lock contention drops to zero in PostgreSQL monitoring.
3. Validate that `POST /v1/orders` p99 latency normalizes below 800ms.
