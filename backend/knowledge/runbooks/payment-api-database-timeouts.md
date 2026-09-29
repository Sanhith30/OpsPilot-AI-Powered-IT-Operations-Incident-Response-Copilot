# Payment API Database Timeouts

## Symptoms
The Payment API may return elevated 5xx responses when database connections cannot be established within the configured timeout.
Common symptoms include:
- Increased request latency
- Database connection timeout errors
- Failed payment requests

## Investigation
Check the application logs for database timeout messages.
Check whether the database connection pool is exhausted.
Review recent deployments to determine whether a new release coincided with the increase in failures.

## Mitigation
Verify database availability.
Check connection pool usage.
If the issue began immediately after a production deployment, follow the deployment rollback procedure.

## Verification
Confirm that database timeout errors have stopped.
Confirm that API error rate returns to the normal operating range.
Confirm successful payment requests.
