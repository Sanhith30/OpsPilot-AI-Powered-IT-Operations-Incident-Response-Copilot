# Kubernetes Pod CrashLoopBackOff and OOMKilled Restart Procedure

## Overview
Standard operational procedure for diagnosing and recovering Kubernetes workloads stuck in restart loops or terminated due to memory exhaustion.

## Symptoms
- Pod status displays `CrashLoopBackOff`, `Error`, or `OOMKilled`
- Kubernetes events show container termination with exit code 137 (OOM) or 1 (application failure)
- Horizontal Pod Autoscaler (HPA) failing to scale healthy replicas
- Cluster alerting firing for `KubePodCrashLooping`

## Investigation
1. Retrieve pod termination details:
   ```bash
   kubectl describe pod <pod-name> -n <namespace>
   ```
   Inspect `Last State` -> `Terminated` -> `Reason` and `Exit Code`.
2. Check previous container logs prior to termination:
   ```bash
   kubectl logs <pod-name> -n <namespace> --previous --tail=100
   ```
3. Check container cgroup memory limits against application memory profile in Datadog/Prometheus.
4. Verify if liveness or readiness probes are failing due to slow application startup.

## Remediation Steps
1. For `OOMKilled` (Exit Code 137):
   - Increase `resources.limits.memory` and `resources.requests.memory` in the deployment Helm values or YAML manifest.
   - Adjust JVM `-Xmx` or Node.js `--max-old-space-size` heap limits to 75% of the container memory limit.
2. For failing startup/readiness probes:
   - Increase `initialDelaySeconds` or `periodSeconds` on the readiness probe.
3. Perform a safe rolling restart:
   ```bash
   kubectl rollout restart deployment/<deployment-name> -n <namespace>
   ```

## Verification
1. Ensure all pods in deployment reach `Running` status with ready condition `1/1`.
2. Confirm container restart count ceases incrementing over a 15-minute observation window.
3. Validate memory usage does not exceed 80% of configured container memory limits.
