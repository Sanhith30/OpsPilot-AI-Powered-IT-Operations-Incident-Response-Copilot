"""
High-volume enterprise operational dataset generator for OpsPilot.

Generates ~190,000+ realistic operational rows:
  - 250 Incidents (preserving Incident #1)
  - 5,000 Incident Events linked to incidents
  - 1,000 Remediation & Maintenance Tickets (TICK-XXXXXXXX)
  - 800 Deployments across all 6 microservices
  - 120,000 Application Logs (INFO / WARN / ERROR with realistic trace IDs & messages)
  - 60,000 Service Metrics (CPU, memory, latency, RPS, connection pools)
  - 5,000 Audit Logs tracking operations

Maintains strict referential integrity with core.services, core.teams, and core.users.
Uses batched multi-row SQL INSERTs for high-throughput population in seconds.
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

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

NOW = datetime.now(timezone.utc)

SERVICES = [
    (1, "Payment API", "payment-api"),
    (2, "Order Service", "order-service"),
    (3, "Authentication Service", "auth-service"),
    (4, "Fraud Detection Service", "fraud-service"),
    (5, "Notification Service", "notification-service"),
    (6, "Product Catalog Service", "catalog-service"),
]

TEAMS = [1, 2, 3, 4, 5]
USERS = [1, 2, 3, 4]

SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
SEVERITY_WEIGHTS = [0.45, 0.35, 0.15, 0.05]

INCIDENT_TITLES = [
    "Elevated HTTP 504 Gateway Timeouts on checkout endpoints",
    "HikariCP database connection pool exhaustion under load",
    "Memory leak detected in JVM heap during heavy batch processing",
    "Redis cluster replica failover causing temporary read latency spike",
    "Upstream payment gateway 502 Bad Gateway response surge",
    "Authentication JWT validation failure after key rotation",
    "Kafka consumer group lag exceeded 15,000 messages",
    "Circuit breaker OPEN on fraud verification downstream",
    "Container OOMKilled in Kubernetes pod replica set",
    "High CPU utilization > 92% sustained for 15 minutes",
    "PostgreSQL active transaction lock contention on orders table",
    "Stale cache invalidation causing thundering herd on catalog service",
    "Rate limiter rejecting legitimate API traffic due to misconfiguration",
    "Elasticsearch indexing buffer stalled causing log ingestion delay",
    "SSL/TLS certificate expiration warning in ingress controller",
    "DNS resolution flapping on internal consul service discovery",
    "Disk utilization on persistent volume exceeded 88% threshold",
    "gRPC connection drop rate elevated between order and payment services",
    "Stripe webhook delivery failure rate elevated above 12%",
    "Deadlock detected on concurrent inventory update queries",
]

ROOT_CAUSES = [
    "HikariCP connection pool configuration was lowered from 50 to 5 in deployment template.",
    "Unindexed foreign key query caused sequential table scans during peak traffic.",
    "Third-party webhook provider experienced degraded network routing.",
    "Stale cache entries overwhelmed primary database after Redis eviction spike.",
    "Memory leak in async task executor threads prevented garbage collection.",
    "Incorrect IAM role boundary revoked KMS decryption permissions temporarily.",
    "Upstream payment processor network partition caused TLS timeout retries.",
    "Sudden traffic surge from marketing campaign triggered concurrency limits.",
]

LOG_TEMPLATES_INFO = [
    "HTTP GET /api/v1/health returned 200 in {lat}ms",
    "Processed request for user_id={uid} with status 200 OK (size: {sz} bytes)",
    "Database connection checked out from pool in {lat}ms",
    "Cache HIT for key '{key}' — latency {lat}ms",
    "Dispatched async task task_id={tid} to worker queue",
    "Successfully validated bearer authorization token for user_id={uid}",
    "Heartbeat signal sent to service registry (status: HEALTHY)",
    "Payment authorization approved for transaction_id={txid} (amount: ${amt})",
    "Order order_id={oid} transitioned to status CONFIRMED",
    "Notification email queued for delivery to recipient_id={uid}",
]

LOG_TEMPLATES_WARN = [
    "Connection acquisition took {lat}ms, approaching threshold (500ms)",
    "Circuit breaker HALF-OPEN for downstream dependency {dep}",
    "Cache MISS for key '{key}', fetching from primary database",
    "Request rate for IP {ip} approaching rate limit bucket (85% consumed)",
    "Slow query detected: SELECT * FROM {tbl} took {lat}ms",
    "Worker queue depth ({depth} messages) exceeds target threshold (100)",
    "TLS handshake retry required for upstream host {host}",
    "JVM heap usage at {pct}% of max memory allocation",
]

LOG_TEMPLATES_ERROR = [
    "HikariCP pool-1 - Connection is not available, request timed out after {lat}ms",
    "HTTP 504 Gateway Timeout while calling downstream service {dep}",
    "psycopg2.OperationalError: server closed the connection unexpectedly",
    "Circuit breaker OPEN: {dep} failed 5 consecutive health checks",
    "Transaction rolled back due to serialization deadlock on {tbl}",
    "Failed to authenticate request: JWT signature verification expired",
    "Upstream HTTP 502 Bad Gateway from gateway provider endpoint",
    "java.lang.OutOfMemoryError: Java heap space during batch deserialization",
    "KafkaException: Failed to send batch to broker (Broker: Leader not available)",
    "RedisConnectionException: Read timed out after 3000ms against primary node",
]

METRIC_NAMES = [
    ("cpu_utilization_percent", "%", 15.0, 95.0),
    ("memory_utilization_percent", "%", 40.0, 92.0),
    ("http_requests_per_second", "req/s", 50.0, 1200.0),
    ("http_request_duration_p95_ms", "ms", 12.0, 650.0),
    ("http_request_duration_p99_ms", "ms", 25.0, 2400.0),
    ("http_5xx_error_rate_percent", "%", 0.0, 18.0),
    ("db_connection_pool_active", "connections", 2.0, 48.0),
    ("db_connection_pool_wait_ms", "ms", 1.0, 450.0),
]


def chunk_list(lst: list, chunk_size: int):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def generate_enterprise_data():
    db = SessionLocal()
    print("Starting OpsPilot Enterprise Operational Data Generation...")
    start_time = datetime.now()

    try:
        # =================================================================== #
        # 1. Historical Incidents (Target: 300 total, preserving Incident #1) #
        # =================================================================== #
        print("\n[1/7] Generating Historical Incidents (target: 300)...")
        existing_incidents_count = db.execute(text("SELECT COUNT(*) FROM core.incidents")).scalar()
        all_incident_ids = [r[0] for r in db.execute(text("SELECT incident_id FROM core.incidents")).fetchall()]
        
        if existing_incidents_count < 300:
            next_inc_id = max(all_incident_ids, default=0) + 1
            new_incidents = []
            for i in range(300 - existing_incidents_count):
                svc_id, svc_name, _ = random.choice(SERVICES)
                days_ago = random.uniform(1.0, 360.0)
                started_at = NOW - timedelta(days=days_ago)
                detected_at = started_at + timedelta(minutes=random.uniform(2.0, 15.0))
                duration_hours = random.uniform(0.5, 8.0)
                resolved_at = detected_at + timedelta(hours=duration_hours)

                severity = random.choices(SEVERITIES, weights=SEVERITY_WEIGHTS)[0]
                status = "CLOSED" if days_ago > 7 else random.choice(["RESOLVED", "CLOSED"])

                title = random.choice(INCIDENT_TITLES)
                root_cause = random.choice(ROOT_CAUSES)
                impact = f"Degraded performance on {svc_name} affecting approx {random.randint(50, 4500)} user sessions."

                new_incidents.append({
                    "incident_number": f"INC-{next_inc_id + i:05d}",
                    "service_id": svc_id,
                    "title": f"{svc_name}: {title}",
                    "description": f"Production incident detected via automated SLO monitors. {impact}",
                    "severity": severity,
                    "status": status,
                    "started_at": started_at,
                    "detected_at": detected_at,
                    "resolved_at": resolved_at,
                    "assigned_team_id": random.choice(TEAMS),
                    "assigned_user_id": random.choice(USERS),
                    "impact_summary": impact,
                    "root_cause": root_cause,
                })

            for chunk in chunk_list(new_incidents, 100):
                db.execute(
                    text("""
                        INSERT INTO core.incidents (
                            incident_number, service_id, title, description,
                            severity, status, started_at, detected_at, resolved_at,
                            assigned_team_id, assigned_user_id, impact_summary, root_cause
                        ) VALUES (
                            :incident_number, :service_id, :title, :description,
                            :severity, :status, :started_at, :detected_at, :resolved_at,
                            :assigned_team_id, :assigned_user_id, :impact_summary, :root_cause
                        )
                    """),
                    chunk,
                )
            db.commit()
            all_incident_ids = [r[0] for r in db.execute(text("SELECT incident_id FROM core.incidents")).fetchall()]
            print(f"  -> Generated {len(new_incidents)} incidents. Total incidents in DB: {len(all_incident_ids)}")
        else:
            print(f"  -> Incidents already populated ({existing_incidents_count} incidents exist).")

        # =================================================================== #
        # 2. Incident Events (Target: ~6,000)                                 #
        # =================================================================== #
        print("\n[2/7] Generating Incident Timeline Events (target: ~6,000)...")
        existing_events = db.execute(text("SELECT COUNT(*) FROM core.incident_events")).scalar()
        if existing_events < 5000:
            event_types = [
                ("METRIC_THRESHOLD_EXCEEDED", "SLO threshold breach: high latency on primary endpoints"),
                ("LOG_ANOMALY_DETECTED", "Log pattern anomaly: elevated HTTP 504 timeouts"),
                ("DEPLOYMENT_DETECTED", "Recent service deployment identified in incident window"),
                ("MITIGATION_APPLIED", "Remediation action executed: pool scaled and workers restarted"),
                ("STATUS_CHANGED", "Incident status transitioned to INVESTIGATING"),
                ("ENGINEER_ASSIGNED", "On-call SRE assigned to incident triage"),
                ("APPROVAL_REQUESTED", "Human approval requested for automated deployment rollback"),
                ("APPROVAL_GRANTED", "Approval granted by operations lead"),
            ]


            new_events = []
            for inc_id in all_incident_ids:
                num_events = random.randint(15, 25)
                inc_row = db.execute(
                    text("SELECT started_at, resolved_at FROM core.incidents WHERE incident_id = :id"),
                    {"id": inc_id},
                ).fetchone()
                inc_start = inc_row[0] if inc_row else NOW - timedelta(days=10)

                for step in range(num_events):
                    ev_type, ev_msg = random.choice(event_types)
                    ev_time = inc_start + timedelta(minutes=step * random.uniform(3.0, 12.0))
                    metadata = {
                        "event_type": ev_type,
                        "step": step,
                        "error_rate": round(random.uniform(5.0, 45.0), 2) if "SPIKE" in ev_type or "FAILURE" in ev_type else 0.0,
                        "latency_ms": round(random.uniform(120.0, 3200.0), 1),
                    }
                    new_events.append({
                        "incident_id": inc_id,
                        "event_type": ev_type,
                        "description": ev_msg,
                        "event_time": ev_time,
                        "created_by": random.choice(USERS),
                        "metadata": json.dumps(metadata),
                    })

            for chunk in chunk_list(new_events, 1000):
                db.execute(
                    text("""
                        INSERT INTO core.incident_events (
                            incident_id, event_type, event_message, event_timestamp, created_by, metadata
                        ) VALUES (
                            :incident_id, :event_type, :description, :event_time, :created_by, CAST(:metadata AS jsonb)
                        )
                    """),
                    chunk,
                )
            db.commit()
            total_events = db.execute(text("SELECT COUNT(*) FROM core.incident_events")).scalar()
            print(f"  -> Generated {len(new_events)} incident events. Total events in DB: {total_events}")
        else:
            print(f"  -> Incident events already populated ({existing_events} exist).")

        # =================================================================== #
        # 3. Tickets (Target: ~1,200)                                         #
        # =================================================================== #
        print("\n[3/7] Generating Operational Tickets (target: ~1,200)...")
        existing_tickets = db.execute(text("SELECT COUNT(*) FROM core.tickets")).scalar()
        if existing_tickets < 1000:
            new_tickets = []
            ticket_priorities = ["LOW", "MEDIUM", "HIGH", "URGENT"]
            ticket_statuses = ["OPEN", "IN_PROGRESS", "BLOCKED", "RESOLVED", "CLOSED"]
            for inc_id in all_incident_ids[:300]:
                num_tix = random.randint(3, 5)
                for _ in range(num_tix):
                    t_num = f"TICK-{uuid.uuid4().hex[:8].upper()}"
                    prio = random.choice(ticket_priorities)
                    stat = random.choice(ticket_statuses)
                    new_tickets.append({
                        "ticket_number": t_num,
                        "incident_id": inc_id,
                        "title": f"Follow-up remediation for Incident #{inc_id}: {random.choice(INCIDENT_TITLES)[:60]}",
                        "description": "Generated by SRE automation: investigate root cause and apply permanent mitigation.",
                        "priority": prio,
                        "status": stat,
                        "assigned_team_id": random.choice(TEAMS),
                        "assigned_user_id": random.choice(USERS),
                        "created_by": random.choice(USERS),
                    })

            for chunk in chunk_list(new_tickets, 500):
                db.execute(
                    text("""
                        INSERT INTO core.tickets (
                            ticket_number, incident_id, title, description, priority,
                            status, assigned_team_id, assigned_user_id, created_by
                        ) VALUES (
                            :ticket_number, :incident_id, :title, :description, :priority,
                            :status, :assigned_team_id, :assigned_user_id, :created_by
                        )
                    """),
                    chunk,
                )
            db.commit()
            total_tickets = db.execute(text("SELECT COUNT(*) FROM core.tickets")).scalar()
            print(f"  -> Generated {len(new_tickets)} tickets. Total tickets in DB: {total_tickets}")
        else:
            print(f"  -> Tickets already populated ({existing_tickets} exist).")

        # =================================================================== #
        # 4. Deployments (Target: ~800)                                       #
        # =================================================================== #
        print("\n[4/7] Generating Historical Deployments (target: ~800)...")
        existing_deps = db.execute(text("SELECT COUNT(*) FROM core.deployments")).scalar()
        if existing_deps < 500:
            new_deployments = []
            for svc_id, _, _ in SERVICES:
                for v_major in range(1, 4):
                    for v_minor in range(0, 15):
                        for v_patch in range(0, 3):
                            version = f"v{v_major}.{v_minor}.{v_patch}"
                            dep_days_ago = random.uniform(1.0, 360.0)
                            started_at = NOW - timedelta(days=dep_days_ago)
                            completed_at = started_at + timedelta(minutes=random.uniform(4.0, 20.0))
                            env = random.choices(["production", "staging"], weights=[0.8, 0.2])[0]
                            dtype = random.choice(["NORMAL", "HOTFIX", "ROLLBACK", "EMERGENCY"])
                            trigger = random.choice(["MANUAL", "CI_CD", "AUTOMATED"])
                            status = random.choices(["SUCCESS", "FAILED", "CANCELLED"], weights=[0.85, 0.08, 0.07])[0]

                            new_deployments.append({
                                "service_id": svc_id,
                                "version": version,
                                "environment": env,
                                "commit_hash": uuid.uuid4().hex[:12],
                                "deployment_type": dtype,
                                "trigger_type": trigger,
                                "status": status,
                                "started_at": started_at,
                                "completed_at": completed_at,
                                "deployed_by": random.choice(USERS),
                            })

            for chunk in chunk_list(new_deployments, 300):
                db.execute(
                    text("""
                        INSERT INTO core.deployments (
                            service_id, version, environment, commit_hash, deployment_type,
                            trigger_type, status, started_at, completed_at, deployed_by
                        ) VALUES (
                            :service_id, :version, :environment, :commit_hash, :deployment_type,
                            :trigger_type, :status, :started_at, :completed_at, :deployed_by
                        )
                    """),
                    chunk,
                )
            db.commit()
            total_deployments = db.execute(text("SELECT COUNT(*) FROM core.deployments")).scalar()
            print(f"  -> Generated {len(new_deployments)} deployments. Total deployments in DB: {total_deployments}")
        else:
            print(f"  -> Deployments already populated ({existing_deps} exist).")


        # =================================================================== #
        # 5. Application Logs (Target: 120,000)                               #
        # =================================================================== #
        print("\n[5/7] Generating Structured Application Logs (target: 120,000)...")
        existing_logs = db.execute(text("SELECT COUNT(*) FROM core.app_logs")).scalar()
        if existing_logs < 100000:
            log_levels = ["INFO", "WARNING", "ERROR"]
            log_weights = [0.82, 0.12, 0.06]

            total_target_logs = 120000
            logs_batch = []
            batch_count = 0

            for i in range(total_target_logs):
                svc_id, svc_name, svc_key = random.choice(SERVICES)
                level = random.choices(log_levels, weights=log_weights)[0]
                trace_id = uuid.uuid4().hex
                span_id = uuid.uuid4().hex[:16]
                log_time = NOW - timedelta(days=random.uniform(0.01, 30.0), seconds=random.randint(0, 86400))

                lat = random.randint(5, 850)
                uid = random.randint(1001, 9999)
                sz = random.randint(128, 4096)
                amt = round(random.uniform(9.99, 499.99), 2)
                host = f"ip-10-0-{svc_id}-{random.randint(10, 250)}.ec2.internal"

                if level == "INFO":
                    msg_tmpl = random.choice(LOG_TEMPLATES_INFO)
                elif level == "WARNING":
                    msg_tmpl = random.choice(LOG_TEMPLATES_WARN)
                else:
                    msg_tmpl = random.choice(LOG_TEMPLATES_ERROR)

                msg = msg_tmpl.format(
                    lat=lat, uid=uid, sz=sz, amt=amt,
                    key=f"cache:{svc_key}:{uid}",
                    tid=f"task-{random.randint(100, 999)}",
                    txid=f"tx-{uuid.uuid4().hex[:8]}",
                    oid=f"ord-{random.randint(10000, 99999)}",
                    dep=random.choice(["database-primary", "payment-gateway", "fraud-detection", "redis-session"]),
                    ip=f"192.168.1.{random.randint(1, 254)}",
                    tbl="core.transactions",
                    depth=random.randint(50, 400),
                    host=host,
                    pct=random.randint(75, 96),
                )

                extra_data = {
                    "service": svc_key,
                    "latency_ms": lat,
                    "environment": "Production",
                    "request_id": str(uuid.uuid4()),
                }

                logs_batch.append({
                    "service_id": svc_id,
                    "service_name": svc_key,
                    "level": level,
                    "message": msg,
                    "logger_name": f"opspilot.{svc_key}",
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "host": host,
                    "environment": "Production",
                    "extra": json.dumps(extra_data),
                    "logged_at": log_time,
                })

                if len(logs_batch) >= 4000:
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
                    batch_count += len(logs_batch)
                    logs_batch.clear()
                    print(f"    ... {batch_count:,} / {total_target_logs:,} logs inserted", end="\r")

            if logs_batch:
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
                batch_count += len(logs_batch)

            total_logs = db.execute(text("SELECT COUNT(*) FROM core.app_logs")).scalar()
            print(f"\n  -> Completed application logs generation. Total app_logs in DB: {total_logs:,}")
        else:
            print(f"  -> Application logs already populated ({existing_logs:,} exist).")

        # =================================================================== #
        # 6. Service Metrics (Target: 60,000)                                 #
        # =================================================================== #
        print("\n[6/7] Generating Service Telemetry Metrics (target: 60,000)...")
        existing_metrics = db.execute(text("SELECT COUNT(*) FROM core.service_metrics")).scalar()
        if existing_metrics < 50000:
            total_target_metrics = 60000
            metrics_batch = []
            metrics_count = 0

            for i in range(total_target_metrics):
                svc_id, _, svc_key = random.choice(SERVICES)
                metric_name, unit, val_min, val_max = random.choice(METRIC_NAMES)
                val = round(random.uniform(val_min, val_max), 3)
                rec_time = NOW - timedelta(days=random.uniform(0.01, 30.0), seconds=random.randint(0, 86400))
                inst_id = f"i-{svc_key}-{random.randint(1, 4)}"

                dims = {
                    "service": svc_key,
                    "instance": inst_id,
                    "env": "Production",
                    "region": "us-east-1",
                }

                metrics_batch.append({
                    "service_id": svc_id,
                    "service_name": svc_key,
                    "instance_id": inst_id,
                    "environment": "Production",
                    "metric_name": metric_name,
                    "metric_value": val,
                    "unit": unit,
                    "dimensions": json.dumps(dims),
                    "recorded_at": rec_time,
                })

                if len(metrics_batch) >= 4000:
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
                    metrics_count += len(metrics_batch)
                    metrics_batch.clear()
                    print(f"    ... {metrics_count:,} / {total_target_metrics:,} metrics inserted", end="\r")

            if metrics_batch:
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
                metrics_count += len(metrics_batch)

            total_metrics = db.execute(text("SELECT COUNT(*) FROM core.service_metrics")).scalar()
            print(f"\n  -> Completed service metrics generation. Total service_metrics in DB: {total_metrics:,}")
        else:
            print(f"  -> Service metrics already populated ({existing_metrics:,} exist).")

        # =================================================================== #
        # 7. Audit Logs (Target: ~5,000)                                      #
        # =================================================================== #
        print("\n[7/7] Generating Audit Logs (target: ~5,000)...")
        existing_audits = db.execute(text("SELECT COUNT(*) FROM core.audit_logs")).scalar()
        if existing_audits < 4000:
            actions = [
                ("INVESTIGATION_START", "investigation", "SUCCESS"),
                ("INVESTIGATION_COMPLETE", "investigation", "SUCCESS"),
                ("TICKET_CREATED", "ticket", "SUCCESS"),
                ("TICKET_STATUS_UPDATED", "ticket", "SUCCESS"),
                ("REMEDIATION_PLAN_PROPOSED", "remediation", "SUCCESS"),
                ("REMEDIATION_APPROVED", "remediation", "SUCCESS"),
                ("USER_LOGIN", "session", "SUCCESS"),
                ("CONFIG_UPDATED", "system", "SUCCESS"),
                ("SQL_QUERY_EXECUTED", "database", "SUCCESS"),
                ("SQL_BLOCKED_UNAUTHORIZED", "database", "DENIED"),
            ]

            audit_batch = []
            for _ in range(5000):
                act, rtype, res = random.choice(actions)
                audit_batch.append({
                    "actor_user_id": random.choice(USERS),
                    "actor_type": random.choice(["USER", "AI", "SYSTEM"]),
                    "action": act,
                    "resource_type": rtype,
                    "resource_id": f"res-{uuid.uuid4().hex[:8]}",
                    "incident_id": random.choice(all_incident_ids[:50]),
                    "investigation_id": None,
                    "ticket_id": None,
                    "action_result": res,
                    "request_id": str(uuid.uuid4()),
                    "ip_address": f"10.0.{random.randint(1, 5)}.{random.randint(1, 250)}",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OpsPilot/0.2.0",
                    "details": json.dumps({"action": act, "result": res}),
                })

            for chunk in chunk_list(audit_batch, 1000):
                db.execute(
                    text("""
                        INSERT INTO core.audit_logs (
                            actor_user_id, actor_type, action, resource_type, resource_id,
                            incident_id, investigation_id, ticket_id, action_result,
                            request_id, ip_address, user_agent, details
                        ) VALUES (
                            :actor_user_id, :actor_type, :action, :resource_type, :resource_id,
                            :incident_id, :investigation_id, :ticket_id, :action_result,
                            :request_id, CAST(:ip_address AS inet), :user_agent, CAST(:details AS jsonb)
                        )
                    """),
                    chunk,
                )
            db.commit()

            total_audits = db.execute(text("SELECT COUNT(*) FROM core.audit_logs")).scalar()
            print(f"  -> Generated {len(audit_batch)} audit logs. Total audit_logs in DB: {total_audits:,}")
        else:
            print(f"  -> Audit logs already populated ({existing_audits:,} exist).")

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n============================================================")
        print(f"Enterprise Data Generation Completed in {elapsed:.1f} seconds!")
        print(f"============================================================")

    except Exception as exc:
        db.rollback()
        print(f"ERROR: Enterprise data generation failed: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    generate_enterprise_data()
