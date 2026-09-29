# Redis Cache Connection Timeout and Eviction Failure Runbook

## Symptoms
Applications connecting to the Redis cluster report connection timeouts, elevated latency, and command failures.
Common symptoms include:
- `RedisConnectionException: Connection timed out after 3000ms`
- `OOM command not allowed when used memory > 'maxmemory'`
- Cache miss rate surging to 100% across dependent microservices
- Read-only replica errors (`READONLY You can't write against a read only replica`)

## Investigation
1. Execute `redis-cli -h <host> info memory` to check `used_memory` versus `maxmemory`.
2. Inspect `evicted_keys` and `instantaneous_ops_per_sec` in Redis metrics.
3. Check Redis sentinel or cluster nodes for unexpected failovers or network partition events.
4. Identify which keyspace is consuming excessive memory using `redis-cli --bigkeys`.

## Mitigation
1. If memory is exhausted, temporarily increase `maxmemory` or change eviction policy to `volatile-lru` or `allkeys-lru`.
2. Purge non-critical expired caches using targeted SCAN and UNLINK commands.
3. If primary node is partitioned or frozen, trigger manual sentinel failover: `redis-cli sentinel failover <master-name>`.

## Verification
1. Ensure Redis memory utilization stabilizes below 80% of maxmemory.
2. Confirm Redis command latency returns to sub-millisecond ranges (< 5ms).
3. Validate microservice cache hit ratios recover above 85%.
