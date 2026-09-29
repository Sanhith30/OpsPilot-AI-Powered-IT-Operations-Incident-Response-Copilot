#!/usr/bin/env python3
"""
OpsPilot Integration Test Fixture Seeder
Seeds deterministic, idempotent test datasets for LogHub, OpenTelemetry,
and microservices telemetry into core.app_logs and core.service_metrics.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg


def _to_psycopg_conninfo(database_url: str) -> str:
    for prefix in (
        "postgresql+psycopg://",
        "postgresql://",
        "postgres://",
    ):
        if database_url.startswith(prefix):
            return "postgresql://" + database_url[len(prefix):]
    return database_url


def seed_test_data() -> None:
    raw_url = os.environ.get("DATABASE_URL") or os.environ.get("DB_URL")
    if not raw_url:
        for env_path in [Path("backend/.env"), Path(".env")]:
            if env_path.exists():
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip()
                        if k in ("DATABASE_URL", "DB_URL"):
                            raw_url = v
                        elif k not in os.environ:
                            os.environ[k] = v

    if not raw_url:
        import urllib.parse
        db_user = os.environ.get("DB_USER") or os.environ.get("POSTGRES_USER", "postgres")
        db_pass = os.environ.get("DB_PASSWORD") or os.environ.get("POSTGRES_PASSWORD", "postgrespassword")
        db_host = os.environ.get("DB_HOST") or os.environ.get("POSTGRES_HOST", "127.0.0.1")
        db_port = os.environ.get("DB_PORT") or os.environ.get("POSTGRES_PORT", "5432")
        db_name = os.environ.get("DB_NAME") or os.environ.get("POSTGRES_DB", "opspilot")
        raw_url = f"postgresql://{urllib.parse.quote_plus(db_user)}:{urllib.parse.quote_plus(db_pass)}@{db_host}:{db_port}/{db_name}"

    conninfo = _to_psycopg_conninfo(raw_url)
    print(f"[*] Connecting to database to seed integration fixtures...")

    now = datetime.now(timezone.utc)

    with psycopg.connect(conninfo, autocommit=True) as conn:
        with conn.cursor() as cur:
            # 1. Seed LogHub records (Target: 1,200 records across HDFS, Linux, BGL, Hadoop)
            cur.execute("SELECT COUNT(*) FROM core.app_logs WHERE extra->>'source' = 'loghub';")
            existing_loghub = cur.fetchone()[0]
            print(f"[*] Existing LogHub logs in DB: {existing_loghub}")

            if existing_loghub < 1000:
                print("[+] Seeding 1,200 structured LogHub logs across datasets (HDFS, Linux, BGL, Hadoop)...")
                loghub_rows = []

                # Linux (300 logs) -> auth-service
                for i in range(300):
                    t = now - timedelta(minutes=i % 300)
                    msg = (
                        f"Jun 23 23:30:{i % 60:02d} server-host sshd[{1000 + i}]: "
                        f"Failed password for invalid user root from 192.168.1.{10 + (i % 50)} port 4522 sshd: authentication failure"
                        if i % 3 == 0 else
                        f"Jun 23 23:30:{i % 60:02d} server-host kernel: [12345.{i}] Linux system event code={i} ok"
                    )
                    loghub_rows.append((
                        3, "auth-service", "ERROR" if i % 3 == 0 else "INFO",
                        msg, "syslog.auth", uuid.uuid4().hex[:16], "server-host", "Production",
                        json.dumps({"source": "loghub", "dataset": "Linux", "log_type": "syslog"}),
                        t
                    ))

                # HDFS (300 logs) -> order-service
                for i in range(300):
                    t = now - timedelta(minutes=i % 300)
                    msg = (
                        f"081109 203518 {i} INFO dfs.DataNode$PacketResponder: "
                        f"PacketResponder 1 for block blk_-1608999832728717387 terminating"
                        if i % 4 == 0 else
                        f"081109 203518 {i} INFO dfs.FSNamesystem: BLOCK* NameSystem.allocateBlock: /user/hadoop/data_{i}.txt"
                    )
                    loghub_rows.append((
                        2, "order-service", "INFO",
                        msg, "dfs.DataNode", uuid.uuid4().hex[:16], "hdfs-dn-01", "Production",
                        json.dumps({"source": "loghub", "dataset": "HDFS", "log_type": "hdfs"}),
                        t
                    ))

                # BGL (300 logs) -> payment-api
                for i in range(300):
                    t = now - timedelta(minutes=i % 300)
                    msg = (
                        f"instruction cache parity error detected on node R02-M1-N0-C:J12-U01 processor {i % 4}"
                        if i % 5 == 0 else
                        f"RAS KERNEL INFO generate_tree: network packet ok rank {i}"
                    )
                    loghub_rows.append((
                        1, "payment-api", "ERROR" if i % 5 == 0 else "INFO",
                        msg, "bgl.kernel", uuid.uuid4().hex[:16], "bgl-rack-02", "Production",
                        json.dumps({"source": "loghub", "dataset": "BGL", "log_type": "bgl"}),
                        t
                    ))

                # Hadoop (300 logs) -> order-service
                for i in range(300):
                    t = now - timedelta(minutes=i % 300)
                    msg = f"Task attempt_200811092030_{i:04d}_m_000000_0 is done."
                    loghub_rows.append((
                        2, "order-service", "INFO",
                        msg, "hadoop.task", uuid.uuid4().hex[:16], "hadoop-master", "Production",
                        json.dumps({"source": "loghub", "dataset": "Hadoop", "log_type": "hadoop"}),
                        t
                    ))

                cur.executemany(
                    """
                    INSERT INTO core.app_logs (
                        service_id, service_name, level, message, logger_name,
                        trace_id, host, environment, extra, logged_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    loghub_rows
                )
                print(f"[+] Successfully seeded {len(loghub_rows)} LogHub logs.")
            else:
                print(f"[~] Skipping LogHub seeding (already present: {existing_loghub}).")

            # 2. Seed OTel Metrics & Correlated Logs
            cur.execute("SELECT COUNT(*) FROM core.service_metrics WHERE dimensions->>'telemetry_source' = 'otel-astronomy-shop';")
            existing_otel_metrics = cur.fetchone()[0]
            print(f"[*] Existing OTel metrics in DB: {existing_otel_metrics}")

            if existing_otel_metrics == 0:
                print("[+] Seeding OpenTelemetry metrics for paymentservice, checkoutservice, and payment-api...")
                otel_services = [
                    (1, "paymentservice"),
                    (1, "payment-api"),
                    (2, "checkoutservice"),
                    (2, "order-service"),
                    (3, "auth-service"),
                ]

                metric_defs = [
                    ("p99_latency_ms", "ms", 120.0),
                    ("error_rate", "%", 2.5),
                    ("request_rate_rps", "rps", 850.0),
                    ("cpu_usage_percent", "%", 45.0),
                    ("memory_usage_mb", "MB", 1024.0),
                    ("db_connection_pool", "connections", 25.0),
                ]

                metric_rows = []
                # Emit metrics across past 24 hours
                for offset in range(0, 1440, 30):
                    rec_time = now - timedelta(minutes=offset)
                    for sid, sname in otel_services:
                        inst = f"otel-pod-{sname}-1"
                        dims = json.dumps({
                            "telemetry_source": "otel-astronomy-shop",
                            "otel.service.name": sname,
                            "k8s.pod.name": inst,
                            "k8s.namespace": "astronomy-shop",
                        })
                        for mname, unit, base_val in metric_defs:
                            metric_rows.append((
                                sid, sname, inst, "Production", mname, base_val + (offset % 10), unit, dims, rec_time
                            ))

                cur.executemany(
                    """
                    INSERT INTO core.service_metrics (
                        service_id, service_name, instance_id, environment,
                        metric_name, metric_value, unit, dimensions, recorded_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    metric_rows
                )
                print(f"[+] Successfully seeded {len(metric_rows)} OTel metrics.")
            else:
                print(f"[~] Skipping OTel metrics seeding (already present: {existing_otel_metrics}).")

            # 3. Seed OTel Logs
            cur.execute("SELECT COUNT(*) FROM core.app_logs WHERE extra->>'telemetry_source' = 'otel-astronomy-shop';")
            existing_otel_logs = cur.fetchone()[0]
            print(f"[*] Existing OTel logs in DB: {existing_otel_logs}")

            if existing_otel_logs == 0:
                print("[+] Seeding OTel structured logs...")
                otel_log_rows = [
                    (
                        2, "checkoutservice", "ERROR",
                        "OTel Trace [c607cdcc] - checkoutservice upstream RPC call failed with StatusCode.UNAVAILABLE (timeout after 2500ms)",
                        "otel.rpc", uuid.uuid4().hex[:16], "otel-pod-checkoutservice-1", "Production",
                        json.dumps({"telemetry_source": "otel-astronomy-shop", "source": "otel-astronomy-shop", "otel.service.name": "checkoutservice"}),
                        now - timedelta(minutes=5)
                    ),
                    (
                        1, "paymentservice", "INFO",
                        "OTel Trace [f501fec4] - paymentservice processed payment request successfully in 45ms",
                        "otel.rpc", uuid.uuid4().hex[:16], "otel-pod-paymentservice-1", "Production",
                        json.dumps({"telemetry_source": "otel-astronomy-shop", "source": "otel-astronomy-shop", "otel.service.name": "paymentservice"}),
                        now - timedelta(minutes=6)
                    ),
                    (
                        1, "payment-api", "ERROR",
                        "Database connection pool saturation: active connections at 94% threshold",
                        "payment.telemetry", uuid.uuid4().hex[:16], "ip-10-0-2-14", "Production",
                        json.dumps({"telemetry_source": "otel-astronomy-shop", "source": "otel-astronomy-shop", "otel.service.name": "payment-api"}),
                        now - timedelta(minutes=10)
                    )
                ]

                cur.executemany(
                    """
                    INSERT INTO core.app_logs (
                        service_id, service_name, level, message, logger_name,
                        trace_id, host, environment, extra, logged_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    otel_log_rows
                )
                print(f"[+] Successfully seeded {len(otel_log_rows)} OTel logs.")
            else:
                print(f"[~] Skipping OTel logs seeding (already present: {existing_otel_logs}).")

    print("[+] All integration test data seeded successfully!")


if __name__ == "__main__":
    seed_test_data()
