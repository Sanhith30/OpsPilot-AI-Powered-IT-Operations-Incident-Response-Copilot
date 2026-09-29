# Standard Operating Procedure for Production Deployment Rollbacks

## Purpose
This Standard Operating Procedure (SOP) governs the mandatory sequence of actions required to safely rollback a failed, degraded, or anomalous production software deployment.

## Rollback Triggers
An immediate rollback must be initiated if any of the following conditions occur within 30 minutes of deployment completion:
- Error rate (HTTP 5xx) increases by more than 1.0% above pre-deployment baseline.
- Service p99 latency degrades by more than 50%.
- Core business transaction success rate falls below 99.5%.
- Critical regression in database connection handling or pool starvation is detected.

## Pre-Rollback Safety Checks
1. Assess database compatibility: Verify whether the deployed release executed non-backwards-compatible schema migrations (e.g., column removals or table renames). If breaking migrations were applied, do not execute a blind container rollback without database migration rollback scripts.
2. Confirm target previous release tag: Retrieve the exact stable git commit SHA and image tag running prior to deployment from the deployment history log.

## Rollback Execution
1. Kubernetes Rollout Undo:
   ```bash
   kubectl rollout undo deployment/<service-name> -n <namespace>
   ```
2. For GitOps / ArgoCD deployments:
   Revert the commit in the deployment repository to the previous stable release tag, or trigger immediate sync of the prior target revision.
3. If canary routing is active, immediately direct 100% of ingress traffic to the stable baseline deployment and terminate the canary pods.

## Post-Rollback Verification
1. Verify pod replacement status:
   ```bash
   kubectl rollout status deployment/<service-name> -n <namespace>
   ```
2. Confirm error rates and latency metrics return to baseline levels.
3. File a deployment failure incident ticket and notify engineering leads.
