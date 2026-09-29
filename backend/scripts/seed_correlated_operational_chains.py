"""
Seed Deeply Correlated Operational Incident Chains for OpsPilot.

Creates 5 end-to-end correlated causal chains following the architecture:
Deployment -> Service -> Metric Spikes -> Error Log Burst -> Incident -> Timeline Events -> Remediation Ticket

Chains implemented:
1. Payment API (Deployment v1.4.2): HikariCP pool exhaustion -> 504 timeouts -> INC-2041 -> TICK-POOL-142
2. Order Service (Deployment v2.1.0): Kafka lag & deadlock -> serialization errors -> INC-2042 -> TICK-KAFKA-210
3. Auth Service (Deployment v1.8.5): JWT key rotation -> signature verification failures -> INC-2043 -> TICK-AUTH-185
4. Fraud Service (Deployment v3.0.1): Memory leak -> OOMKilled crashloop -> INC-2044 -> TICK-OOM-301
5. Catalog Service (Deployment v1.12.0): Redis cache eviction -> thundering herd on DB -> INC-2045 -> TICK-CACHE-112
"""
from __future__ import annotations

import json
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from sqlalchemy import text
from app.db.session import SessionLocal

NOW = datetime.now(timezone.utc)

CORRELATED_CHAINS = [
    {
        "service_id": 1,
        "service_name": "payment-api",
        "deployment_version": "v1.4.2",
        "incident_number": "INC-2041",
        "incident_title": "Payment API critical database connection exhaustion after v1.4.2 rollout",
        "severity": "CRITICAL",
        "root_cause": "HikariCP maximumPoolSize configuration was reduced from 50 to 5 in deployment template.",
        "ticket_number": "TICK-POOL-142",
        "ticket_title": "Rollback deployment v1.4.2 and restore HikariCP pool minimum size to 50",
        "metrics_spike": [
            ("cpu_usage_percent", "%", 88.5),
            ("db_connection_pool", "connections", 49.0),
            ("p99_latency_ms", "ms", 3250.0),
            ("error_rate", "%", 36.4),
        ],
        "log_templates": [
            ("ERROR", "HikariCP pool-1 - Connection is not available, request timed out after 3000ms"),
            ("ERROR", "HTTP 504 Gateway Timeout while calling downstream service database-primary"),
            ("WARNING", "Connection acquisition took 2890ms, approaching threshold (3000ms)"),
            ("ERROR", "psycopg2.OperationalError: connection pool exhausted (active=49, max=50)"),
        ],
        "time_offset_hours": 12,
    },
    {
        "service_id": 2,
        "service_name": "order-service",
        "deployment_version": "v2.1.0",
        "incident_number": "INC-2042",
        "incident_title": "Order Service consumer partition starvation and concurrent update deadlock",
        "severity": "HIGH",
        "root_cause": "Missing index on order_events table caused sequential lock escalation during consumer rebalance.",
        "ticket_number": "TICK-KAFKA-210",
        "ticket_title": "Apply migration for idx_orders_partition and configure pessimistic row locking",
        "metrics_spike": [
            ("error_rate", "%", 19.8),
            ("p99_latency_ms", "ms", 1850.0),
            ("cpu_usage_percent", "%", 74.2),
            ("db_connection_pool", "connections", 38.0),
        ],
        "log_templates": [
            ("ERROR", "KafkaException: Failed to send batch to broker (Broker: Leader not available)"),
            ("ERROR", "Transaction rolled back due to serialization deadlock on core.orders"),
            ("WARNING", "Worker queue depth (18,450 messages) exceeds target threshold (100)"),
            ("ERROR", "ConsumerCoordinator: Commit failed on partition orders-4 due to group rebalance"),
        ],
        "time_offset_hours": 24,
    },
    {
        "service_id": 3,
        "service_name": "auth-service",
        "deployment_version": "v1.8.5",
        "incident_number": "INC-2043",
        "incident_title": "Authentication Service rejected token verification after asymmetric key rotation",
        "severity": "HIGH",
        "root_cause": "Public JWKS key cache ttl was set to 24h, causing ingress proxies to reject freshly minted tokens.",
        "ticket_number": "TICK-AUTH-185",
        "ticket_title": "Distribute updated JWKS public key cache and enforce automated key rotation grace period",
        "metrics_spike": [
            ("error_rate", "%", 44.2),
            ("p99_latency_ms", "ms", 620.0),
            ("request_rate_rps", "rps", 850.0),
        ],
        "log_templates": [
            ("ERROR", "Failed to authenticate request: JWT signature verification expired"),
            ("ERROR", "sshd(pam_unix): authentication failure; logname= uid=0 euid=0 tty=NODEVssh"),
            ("WARNING", "JWKS key id 'k-2026-09' not found in local cache, fallback to remote endpoint"),
            ("ERROR", "HTTP 401 Unauthorized returned for bearer token on /api/v1/auth/verify"),
        ],
        "time_offset_hours": 36,
    },
    {
        "service_id": 4,
        "service_name": "fraud-service",
        "deployment_version": "v3.0.1",
        "incident_number": "INC-2044",
        "incident_title": "Fraud Detection worker pod crash-looping under heap exhaustion",
        "severity": "HIGH",
        "root_cause": "Unbounded array buffer in payload deserializer retained references during async evaluation.",
        "ticket_number": "TICK-OOM-301",
        "ticket_title": "Fix unclosed stream in ML feature vector deserializer and tune JVM MaxRAMPercentage to 75%",
        "metrics_spike": [
            ("memory_usage_mb", "MB", 3850.0),
            ("cpu_usage_percent", "%", 94.8),
            ("error_rate", "%", 28.5),
        ],
        "log_templates": [
            ("ERROR", "java.lang.OutOfMemoryError: Java heap space during batch deserialization"),
            ("CRITICAL", "Container OOMKilled in Kubernetes pod replica set fraud-worker-7c49b"),
            ("WARNING", "JVM heap usage at 96% of max memory allocation (3850MB / 4096MB)"),
            ("ERROR", "Circuit breaker OPEN: fraud-service failed 5 consecutive health checks"),
        ],
        "time_offset_hours": 48,
    },
    {
        "service_id": 6,
        "service_name": "catalog-service",
        "deployment_version": "v1.12.0",
        "incident_number": "INC-2045",
        "incident_title": "Catalog Service cache stampede overwhelming primary database",
        "severity": "MEDIUM",
        "root_cause": "Cache key TTL expiration synchronization caused 15,000 concurrent queries to hit PostgreSQL simultaneously.",
        "ticket_number": "TICK-CACHE-112",
        "ticket_title": "Implement probabilistic early expiration (XFetch) and local in-memory cache layer",
        "metrics_spike": [
            ("p99_latency_ms", "ms", 4850.0),
            ("db_connection_pool", "connections", 48.0),
            ("cpu_usage_percent", "%", 96.5),
        ],
        "log_templates": [
            ("WARNING", "Cache MISS for key 'cache:catalog:top_categories', fetching from primary database"),
            ("ERROR", "Slow query detected: SELECT * FROM core.catalog took 4250ms"),
            ("ERROR", "HTTP 504 Gateway Timeout while calling downstream service catalog-service"),
            ("WARNING", "Redis cluster replica failover causing temporary read latency spike"),
        ],
        "time_offset_hours": 60,
    },
]


def seed_correlated_chains():
    db = SessionLocal()
    print("=" * 65)
    print("Seeding Deeply Correlated Operational Incident Chains...")
    print("=" * 65)

    for chain in CORRELATED_CHAINS:
        t_base = NOW - timedelta(hours=chain["time_offset_hours"])
        t_deploy = t_base - timedelta(minutes=15)
        t_spike = t_base - timedelta(minutes=8)
        t_incident = t_base
        t_resolve = t_base + timedelta(minutes=45)

        svc_id = chain["service_id"]
        svc_name = chain["service_name"]
        dep_version = chain["deployment_version"]
        inc_num = chain["incident_number"]

        print(f"\nProcessing Chain for {svc_name} ({inc_num} / {dep_version})...")

        # 1. Ensure Deployment exists
        existing_dep = db.execute(
            text("SELECT deployment_id FROM core.deployments WHERE service_id = :sid AND version = :ver"),
            {"sid": svc_id, "ver": dep_version},
        ).fetchone()

        if not existing_dep:
            db.execute(
                text("""
                    INSERT INTO core.deployments (
                        service_id, version, environment, commit_hash, deployment_type,
                        trigger_type, status, started_at, completed_at, deployed_by
                    ) VALUES (
                        :sid, :ver, 'production', :commit, 'NORMAL',
                        'CI_CD', 'SUCCESS', :started_at, :completed_at, 1
                    )
                """),
                {
                    "sid": svc_id,
                    "ver": dep_version,
                    "commit": uuid.uuid4().hex[:12],
                    "started_at": t_deploy,
                    "completed_at": t_deploy + timedelta(minutes=6),
                },
            )
            db.commit()
            print(f"  [1/6] Created correlated deployment {dep_version} for {svc_name}")
        else:
            print(f"  [1/6] Correlated deployment {dep_version} already present")

        # 2. Correlated Metrics Spike
        metrics_batch = []
        for m_name, unit, val in chain["metrics_spike"]:
            for step in range(12):  # 12 samples over 30 minutes
                sample_time = t_spike + timedelta(minutes=step * 2.5)
                # Add natural jitter
                sample_val = round(val * random.uniform(0.92, 1.08), 2)
                dims = {
                    "correlation_chain": inc_num,
                    "deployment_version": dep_version,
                    "service": svc_name,
                    "environment": "Production",
                }
                metrics_batch.append({
                    "service_id": svc_id,
                    "service_name": svc_name,
                    "instance_id": f"i-{svc_name}-prod-01",
                    "environment": "Production",
                    "metric_name": m_name,
                    "metric_value": sample_val,
                    "unit": unit,
                    "dimensions": json.dumps(dims),
                    "recorded_at": sample_time,
                })

        db.execute(
            text("""
                INSERT INTO core.service_metrics (
                    service_id, service_name, instance_id, environment,
                    metric_name, metric_value, unit, dimensions, recorded_at
                ) VALUES (
                    :service_id, :service_name, :instance_id, :environment,
                    :metric_name, :metric_value, :unit, CAST(:dimensions AS jsonb), :recorded_at
                )
            """),
            metrics_batch,
        )
        db.commit()
        print(f"  [2/6] Inserted {len(metrics_batch)} correlated telemetry metric samples")

        # 3. Correlated Error Log Burst with shared trace IDs
        logs_batch = []
        shared_trace_id = uuid.uuid4().hex
        for step in range(40):
            lvl, tmpl = random.choice(chain["log_templates"])
            log_time = t_spike + timedelta(minutes=random.uniform(0.5, 25.0))
            logs_batch.append({
                "service_id": svc_id,
                "service_name": svc_name,
                "level": lvl,
                "message": tmpl,
                "logger_name": f"opspilot.{svc_name}",
                "trace_id": shared_trace_id,
                "span_id": uuid.uuid4().hex[:16],
                "host": f"ip-10-0-{svc_id}-12.ec2.internal",
                "environment": "Production",
                "extra": json.dumps({
                    "correlation_chain": inc_num,
                    "deployment_version": dep_version,
                    "source": "causal_chain",
                }),
                "logged_at": log_time,
            })

        db.execute(
            text("""
                INSERT INTO core.app_logs (
                    service_id, service_name, level, message, logger_name,
                    trace_id, span_id, host, environment, extra, logged_at
                ) VALUES (
                    :service_id, :service_name, :level, :message, :logger_name,
                    :trace_id, :span_id, :host, :environment, CAST(:extra AS jsonb), :logged_at
                )
            """),
            logs_batch,
        )
        db.commit()
        print(f"  [3/6] Inserted {len(logs_batch)} correlated error logs with trace_id={shared_trace_id[:8]}")

        # 4. Incident
        existing_inc = db.execute(
            text("SELECT incident_id FROM core.incidents WHERE incident_number = :inum"),
            {"inum": inc_num},
        ).fetchone()

        if not existing_inc:
            db.execute(
                text("""
                    INSERT INTO core.incidents (
                        incident_number, service_id, title, description,
                        severity, status, started_at, detected_at, resolved_at,
                        assigned_team_id, assigned_user_id, impact_summary, root_cause
                    ) VALUES (
                        :inum, :sid, :title, :desc,
                        :sev, 'INVESTIGATING', :started_at, :detected_at, :resolved_at,
                        1, 1, 'Correlated operational incident chain', :rc
                    )
                """),
                {
                    "inum": inc_num,
                    "sid": svc_id,
                    "title": chain["incident_title"],
                    "desc": f"Automated alert: High anomaly score detected on {svc_name} following deployment {dep_version}.",
                    "sev": chain["severity"],
                    "started_at": t_incident,
                    "detected_at": t_incident + timedelta(minutes=2),
                    "resolved_at": t_resolve,
                    "rc": chain["root_cause"],
                },
            )
            db.commit()
            inc_id = db.execute(
                text("SELECT incident_id FROM core.incidents WHERE incident_number = :inum"),
                {"inum": inc_num},
            ).scalar()
            print(f"  [4/6] Created correlated incident {inc_num} (ID: {inc_id})")
        else:
            inc_id = existing_inc[0]
            print(f"  [4/6] Correlated incident {inc_num} already exists (ID: {inc_id})")

        # 5. Timeline Events
        events = [
            ("DEPLOYMENT_DETECTED", f"Service deployment {dep_version} completed on production cluster", t_deploy + timedelta(minutes=6)),
            ("METRIC_THRESHOLD_EXCEEDED", f"SLO threshold breach: error rate and latency spiked on {svc_name}", t_spike + timedelta(minutes=2)),
            ("LOG_ANOMALY_DETECTED", f"Elevated error log frequency with trace {shared_trace_id[:8]}", t_spike + timedelta(minutes=4)),
            ("STATUS_CHANGED", "Incident transitioned to INVESTIGATING by SRE automation", t_incident + timedelta(minutes=2)),
            ("ENGINEER_ASSIGNED", "Assigned to Arun Kumar (On-call Lead)", t_incident + timedelta(minutes=3)),
            ("APPROVAL_REQUESTED", f"Automated remediation proposed: rollback {dep_version}", t_incident + timedelta(minutes=10)),
            ("APPROVAL_GRANTED", "Approval granted by Operations Lead", t_incident + timedelta(minutes=15)),
            ("MITIGATION_APPLIED", "Remediation action executed successfully", t_incident + timedelta(minutes=20)),
        ]

        event_rows = []
        for ev_type, ev_msg, ev_time in events:
            event_rows.append({
                "incident_id": inc_id,
                "event_type": ev_type,
                "description": ev_msg,
                "event_time": ev_time,
                "created_by": 1,
                "metadata": json.dumps({"correlation": inc_num, "trace_id": shared_trace_id}),
            })

        db.execute(
            text("""
                INSERT INTO core.incident_events (
                    incident_id, event_type, event_message, event_timestamp, created_by, metadata
                ) VALUES (
                    :incident_id, :event_type, :description, :event_time, :created_by, CAST(:metadata AS jsonb)
                )
            """),
            event_rows,
        )
        db.commit()
        print(f"  [5/6] Ingested {len(event_rows)} chronological timeline events")

        # 6. Linked Remediation Ticket
        existing_tix = db.execute(
            text("SELECT ticket_id FROM core.tickets WHERE ticket_number = :tnum"),
            {"tnum": chain["ticket_number"]},
        ).fetchone()

        if not existing_tix:
            db.execute(
                text("""
                    INSERT INTO core.tickets (
                        ticket_number, incident_id, title, description, priority,
                        status, assigned_team_id, assigned_user_id, created_by
                    ) VALUES (
                        :tnum, :inc_id, :title, :desc, :prio,
                        'IN_PROGRESS', 1, 1, 1
                    )
                """),
                {
                    "tnum": chain["ticket_number"],
                    "inc_id": inc_id,
                    "title": chain["ticket_title"],
                    "desc": f"Remediation ticket for {inc_num}: {chain['root_cause']}",
                    "prio": "HIGH" if chain["severity"] == "CRITICAL" else "MEDIUM",
                },
            )
            db.commit()
            print(f"  [6/6] Created linked remediation ticket {chain['ticket_number']}")
        else:
            print(f"  [6/6] Remediation ticket {chain['ticket_number']} already exists")

    print("\n" + "=" * 65)
    print("All 5 Correlated Operational Incident Chains Seeded Successfully!")
    print("=" * 65)
    db.close()


if __name__ == "__main__":
    seed_correlated_chains()
