"""
LogHub Real-World Log Ingestion and Verification for OpsPilot.

Pulls standard representative log samples from the public LogHub repository
(HDFS, Linux, BGL, Hadoop), parses them into structured log events with
standard levels, service mappings, and trace IDs, and ingests them into core.app_logs.

Verifies end-to-end retrieval via SearchLogsTool.
"""
from __future__ import annotations

import json
import random
import re
import sys
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from sqlalchemy import text
from app.db.session import SessionLocal
from app.repositories.app_log_repository import AppLogRepository
from app.ai.tools.search_logs import SearchLogsTool, SearchLogsInput

NOW = datetime.now(timezone.utc)

LOGHUB_DATASETS = [
    {
        "name": "HDFS",
        "url": "https://raw.githubusercontent.com/logpai/loghub/master/HDFS/HDFS_2k.log",
        "service_id": 2,
        "service_name": "order-service",
        "default_logger": "dfs.DataNode",
    },
    {
        "name": "Linux",
        "url": "https://raw.githubusercontent.com/logpai/loghub/master/Linux/Linux_2k.log",
        "service_id": 3,
        "service_name": "auth-service",
        "default_logger": "syslog.auth",
    },
    {
        "name": "BGL",
        "url": "https://raw.githubusercontent.com/logpai/loghub/master/BGL/BGL_2k.log",
        "service_id": 1,
        "service_name": "payment-api",
        "default_logger": "kernel.ras",
    },
    {
        "name": "Hadoop",
        "url": "https://raw.githubusercontent.com/logpai/loghub/master/Hadoop/Hadoop_2k.log",
        "service_id": 4,
        "service_name": "fraud-service",
        "default_logger": "hadoop.yarn",
    },
]


def fetch_dataset(url: str) -> list[str]:
    """Fetch log lines from LogHub repository."""
    req = urllib.request.Request(url, headers={"User-Agent": "OpsPilot-LogHub-Ingester/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode("utf-8", errors="replace")
        return [line.strip() for line in content.splitlines() if line.strip()]


def parse_log_line(line: str, dataset_meta: dict) -> dict:
    """Parse raw LogHub log line into structured app_log record."""
    dname = dataset_meta["name"]
    svc_id = dataset_meta["service_id"]
    svc_name = dataset_meta["service_name"]
    logger_name = dataset_meta["default_logger"]

    # Determine log level
    level = "INFO"
    line_upper = line.upper()
    if any(k in line_upper for k in ["FAILURE", "FAILED", "ERROR", "EXCEPTION", "FATAL", "SEVERE"]):
        level = "ERROR"
    elif any(k in line_upper for k in ["WARN", "TIMEOUT", "RETRY", "DROPPED"]):
        level = "WARNING"
    elif "DEBUG" in line_upper:
        level = "DEBUG"

    # Assign realistic recent timestamp
    days_ago = random.uniform(0.01, 14.0)
    logged_at = NOW - timedelta(days=days_ago)

    trace_id = uuid.uuid4().hex
    span_id = uuid.uuid4().hex[:16]
    host = f"ip-10-0-{svc_id}-{random.randint(10, 150)}.ec2.internal"

    extra = {
        "source": "loghub",
        "dataset": dname,
        "raw_preview": line[:150],
        "ingested_by": "OpsPilot-LogHub-Ingester",
    }

    return {
        "service_id": svc_id,
        "service_name": svc_name,
        "level": level,
        "message": line,
        "logger_name": logger_name,
        "trace_id": trace_id,
        "span_id": span_id,
        "host": host,
        "environment": "Production",
        "extra": json.dumps(extra),
        "logged_at": logged_at,
    }


def ingest_loghub_data():
    db = SessionLocal()
    print("=" * 65)
    print("Starting LogHub Real-World Log Ingestion into core.app_logs...")
    print("=" * 65)

    # Check how many loghub logs are already present
    existing_loghub = db.execute(
        text("SELECT COUNT(*) FROM core.app_logs WHERE extra->>'source' = 'loghub'")
    ).scalar()

    if existing_loghub and existing_loghub >= 4000:
        print(f"LogHub logs already present: {existing_loghub:,} rows. Skipping download.")
    else:
        total_ingested = 0
        for ds in LOGHUB_DATASETS:
            print(f"Fetching {ds['name']} sample dataset from {ds['url']}...")
            try:
                raw_lines = fetch_dataset(ds["url"])
                print(f"  -> Fetched {len(raw_lines):,} raw lines from {ds['name']}.")
            except Exception as e:
                print(f"  -> Failed to fetch from {ds['url']}: {e}. Generating realistic synthetic fallback.")
                raw_lines = [
                    f"2026-09-28 12:00:00,100 ERROR {ds['default_logger']}: Connection refused to node-{i}"
                    for i in range(500)
                ]

            parsed_records = [parse_log_line(l, ds) for l in raw_lines]

            # Batch insert
            chunk_size = 500
            for i in range(0, len(parsed_records), chunk_size):
                chunk = parsed_records[i : i + chunk_size]
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
            total_ingested += len(parsed_records)
            print(f"  -> Ingested {len(parsed_records):,} records for {ds['name']} (Service: {ds['service_name']})")

        print(f"\nTotal new LogHub logs ingested: {total_ingested:,}")

    # Verification Step: Test SearchLogsTool
    print("\n" + "=" * 65)
    print("Verifying SearchLogsTool retrieval with LogHub records...")
    print("=" * 65)

    log_repo = AppLogRepository(db=db)
    tool = SearchLogsTool(log_repository=log_repo)

    test_queries = [
        {"keyword": "authentication failure", "desc": "Linux sshd auth failure"},
        {"keyword": "PacketResponder", "desc": "HDFS DataNode PacketResponder"},
        {"keyword": "parity error", "desc": "BGL Kernel cache parity error"},
        {"keyword": "MRAppMaster", "desc": "Hadoop MapReduce AppMaster"},
    ]

    for tq in test_queries:
        res = tool.execute(SearchLogsInput(keyword=tq["keyword"], limit=5))
        logs = res.get("logs", [])
        found = res.get("total_returned", len(logs))
        print(f"Query: '{tq['keyword']}' ({tq['desc']}) -> {found} matches found.")
        assert found > 0, f"Expected matches for keyword '{tq['keyword']}', got 0"
        print(f"  First match: [{logs[0]['service_name']}] [{logs[0]['level']}] {logs[0]['message'][:80]}...")

    print("\nAll LogHub verification searches PASSED successfully!")
    db.close()


if __name__ == "__main__":
    ingest_loghub_data()
