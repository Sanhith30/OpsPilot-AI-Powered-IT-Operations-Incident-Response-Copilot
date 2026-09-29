"""
OpenTelemetry Astronomy Shop Live Telemetry Ingestion Bridge for OpsPilot.

Simulates and ingests realistic high-fidelity OpenTelemetry metrics and structured logs
matching the OpenTelemetry Astronomy Shop demo architecture:
- Services: paymentservice, checkoutservice, cartservice, productcatalogservice, currencyservice, frauddetectionservice
- Telemetry:
    * Metrics: p99_latency_ms, error_rate, request_rate_rps, cpu_usage_percent, memory_usage_mb, db_connection_pool
    * Logs: Structured OTLP log records with trace_id, span_id, resource attributes
- Integrates seamlessly with GetServiceMetricsTool and SearchLogsTool for Copilot investigation.
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
from app.repositories.service_metric_repository import ServiceMetricRepository
from app.repositories.app_log_repository import AppLogRepository
from app.ai.tools.get_service_metrics import GetServiceMetricsTool, GetServiceMetricsInput
from app.ai.tools.search_logs import SearchLogsTool, SearchLogsInput

NOW = datetime.now(timezone.utc)

ASTRONOMY_SERVICES = [
    {"service_id": 1, "service_name": "paymentservice", "alt_name": "payment-api"},
    {"service_id": 2, "service_name": "checkoutservice", "alt_name": "order-service"},
    {"service_id": 4, "service_name": "frauddetectionservice", "alt_name": "fraud-service"},
    {"service_id": 6, "service_name": "productcatalogservice", "alt_name": "catalog-service"},
    {"service_id": 2, "service_name": "cartservice", "alt_name": "order-service"},
    {"service_id": 3, "service_name": "currencyservice", "alt_name": "auth-service"},
]

METRICS_CONFIG = [
    ("p99_latency_ms", "ms", 45.0, 850.0),
    ("error_rate", "%", 0.01, 14.5),
    ("request_rate_rps", "rps", 120.0, 1850.0),
    ("cpu_usage_percent", "%", 15.0, 92.0),
    ("memory_usage_mb", "MB", 256.0, 2048.0),
    ("db_connection_pool", "connections", 5.0, 48.0),
]


def ingest_astronomy_shop_telemetry(num_minutes: int = 60, points_per_min: int = 5):
    """
    Ingest OpenTelemetry Astronomy Shop metrics and correlated logs for the last `num_minutes`.
    """
    db = SessionLocal()
    print("=" * 65)
    print("OpenTelemetry Astronomy Shop Live Telemetry Ingestion")
    print("=" * 65)

    metrics_rows = []
    log_rows = []

    # Check existing count
    existing_otel_metrics = db.execute(
        text("SELECT COUNT(*) FROM core.service_metrics WHERE dimensions->>'telemetry_source' = 'otel-astronomy-shop'")
    ).scalar()

    print(f"Existing OTel Astronomy Shop metrics in DB: {existing_otel_metrics}")

    print(f"Generating live telemetry window ({num_minutes} minutes back)...")
    for minute_offset in range(num_minutes):
        rec_time = NOW - timedelta(minutes=minute_offset)

        for svc in ASTRONOMY_SERVICES:
            # Emit telemetry for both service_name and alt_name for seamless resolution
            for sname in [svc["service_name"], svc["alt_name"]]:
                inst_id = f"otel-pod-{sname}-{random.randint(1, 3)}"

                # 1. Metrics
                for m_name, unit, v_min, v_max in METRICS_CONFIG:
                    val = round(random.uniform(v_min, v_max), 3)
                    dims = {
                        "telemetry_source": "otel-astronomy-shop",
                        "otel.service.name": sname,
                        "k8s.pod.name": inst_id,
                        "k8s.namespace": "astronomy-shop",
                        "deployment.environment": "Production",
                        "net.host.port": 8080,
                    }

                    metrics_rows.append({
                        "service_id": svc["service_id"],
                        "service_name": sname,
                        "instance_id": inst_id,
                        "environment": "Production",
                        "metric_name": m_name,
                        "metric_value": val,
                        "unit": unit,
                        "dimensions": json.dumps(dims),
                        "recorded_at": rec_time,
                    })

                # 2. Correlated Structured Log
                trace_id = uuid.uuid4().hex
                span_id = uuid.uuid4().hex[:16]
                is_error = random.random() < 0.12
                log_level = "ERROR" if is_error else "INFO"

                if is_error:
                    msg = f"OTel Trace [{trace_id[:8]}] - {sname} upstream RPC call failed with StatusCode.UNAVAILABLE (timeout after 2500ms)"
                else:
                    msg = f"OTel Trace [{trace_id[:8]}] - {sname} processed request successfully in {random.randint(12, 180)}ms"

                extra = {
                    "source": "otel-astronomy-shop",
                    "telemetry_source": "otel-astronomy-shop",
                    "otel.trace_id": trace_id,
                    "otel.span_id": span_id,
                    "otel.service.name": sname,
                    "k8s.namespace": "astronomy-shop",
                }

                log_rows.append({
                    "service_id": svc["service_id"],
                    "service_name": sname,
                    "level": log_level,
                    "message": msg,
                    "logger_name": f"opentelemetry.demo.{sname}",
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "host": inst_id,
                    "environment": "Production",
                    "extra": json.dumps(extra),
                    "logged_at": rec_time,
                })

    # Batch insert metrics
    chunk_size = 1000
    for i in range(0, len(metrics_rows), chunk_size):
        chunk = metrics_rows[i : i + chunk_size]
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
            chunk,
        )
    db.commit()
    print(f"  -> Successfully inserted {len(metrics_rows):,} Astronomy Shop metrics rows.")

    # Batch insert logs
    for i in range(0, len(log_rows), chunk_size):
        chunk = log_rows[i : i + chunk_size]
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
            chunk,
        )
    db.commit()
    print(f"  -> Successfully inserted {len(log_rows):,} Astronomy Shop OTel structured log rows.")

    # Verification Step: Query via GetServiceMetricsTool & SearchLogsTool
    print("\n" + "=" * 65)
    print("Verifying Copilot Operational Tools with Astronomy Shop Telemetry...")
    print("=" * 65)

    metric_repo = ServiceMetricRepository(db=db)
    metrics_tool = GetServiceMetricsTool(metric_repository=metric_repo)

    res_metric = metrics_tool.execute(
        GetServiceMetricsInput(service_name="paymentservice", metric_name="p99_latency_ms", lookback_minutes=60)
    )
    print(f"Metrics query: paymentservice p99_latency_ms -> {res_metric.get('total_data_points')} points retrieved.")
    assert res_metric.get("total_data_points", 0) > 0, "Expected metrics data points for paymentservice"
    print(f"  Stats: {res_metric.get('summary', {}).get('p99_latency_ms')}")

    log_repo = AppLogRepository(db=db)
    logs_tool = SearchLogsTool(log_repository=log_repo)

    res_log = logs_tool.execute(
        SearchLogsInput(keyword="StatusCode.UNAVAILABLE", service_name="checkoutservice", limit=5)
    )
    print(f"Logs query: checkoutservice StatusCode.UNAVAILABLE -> {res_log.get('total_returned')} logs retrieved.")
    assert res_log.get("total_returned", 0) > 0, "Expected OTel logs for checkoutservice"
    print(f"  Sample message: {res_log['logs'][0]['message']}")

    print("\nAll OpenTelemetry Demo Telemetry Integrations Verified!")
    db.close()


if __name__ == "__main__":
    ingest_astronomy_shop_telemetry()
