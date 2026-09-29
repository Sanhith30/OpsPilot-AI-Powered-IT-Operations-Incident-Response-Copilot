# Incident Postmortem: Payment API Database Connection Timeout (September 2026)

## Incident Overview
- **Incident ID**: INC-2026-09-PAY
- **Service**: Payment API (`payment-api`)
- **Severity**: SEV-1
- **Duration**: 42 minutes
- **Impact**: ~14,200 payment transactions failed with HTTP 500 / 504 errors; estimated transaction disruption of $420,000.

## Timeline
- `14:02 UTC`: Automated deployment of payment-api release v2.8.1 completed.
- `14:06 UTC`: Alerts fire for `PaymentApiDatabaseTimeout` and `PaymentApi5xxErrorRateHigh`.
- `14:10 UTC`: Incident Commander pages on-call engineering team; SEV-1 declared.
- `14:18 UTC`: On-call engineer inspects database telemetry and discovers connection pool wait times surging past 5000ms.
- `14:26 UTC`: Investigation traces connection starvation to deployment v2.8.1 configuration diff where `pool.max_size` was inadvertently set to 5 instead of 50.
- `14:32 UTC`: IC authorizes immediate deployment rollback to release v2.8.0.
- `14:38 UTC`: Rollback completed across all payment-api pods.
- `14:44 UTC`: Connection wait times drop below 2ms; error rates return to 0.00%; incident resolved.

## Root Cause
Release v2.8.1 introduced an unvalidated environment configuration template change that lowered the HikariCP connection pool maximum size from 50 to 5 connections per pod. Under standard customer transaction concurrency (~350 RPS), all 5 connections were immediately saturated, causing incoming worker threads to block waiting for connection acquisition until reaching the 30-second connection timeout limit.

## Corrective Actions and Preventative Measures
1. **CI Configuration Linting**: Add automated pre-deployment schema validation in CI to verify connection pool sizes against operational runbook baselines (Owner: Platform Team).
2. **Canary Analysis Gate**: Upgrade deployment pipeline to mandate a 10-minute canary evaluation stage with automated rollback on error rate spikes (Owner: Platform Team).
3. **Database Telemetry Refinement**: Separate pool acquisition wait time from query execution duration in standard alerting dashboards (Owner: Database Team).
