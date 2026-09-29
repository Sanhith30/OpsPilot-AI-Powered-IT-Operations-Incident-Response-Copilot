# Authentication Service Token Validation and Database Timeout Runbook

## Symptoms
The Authentication Service returns elevated HTTP 401 Unauthorized responses or HTTP 504 Gateway Timeouts when validating user sessions or issuing JWT tokens.
Common symptoms include:
- Inability for users to log in or refresh tokens
- Increased token validation latency exceeding 2000ms
- Database connection timeout errors connecting to the auth database
- Redis token revocation lookup timeouts

## Investigation
1. Check authentication-service application logs for `DatabaseConnectionTimeoutException` or `TokenVerificationException`.
2. Inspect the auth PostgreSQL database connection pool utilization in Grafana.
3. Check Redis cluster latency to ensure token revocation checks are responding within 5ms.
4. Verify whether JWT signing key rotation occurred recently.

## Mitigation
1. If the auth database connection pool is exhausted, scale connection pool size or restart stuck worker processes.
2. If Redis is unresponsive, verify cluster health and flush non-essential cache namespaces.
3. If an invalid release was deployed, follow the deployment rollback procedure to restore the previous stable auth service version.

## Verification
1. Confirm that token validation error rate drops below 0.01%.
2. Verify token generation endpoint latency p99 is under 50ms.
3. Ensure successful login responses across web and mobile clients.
