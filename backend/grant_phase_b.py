"""
Grant permissions on app_logs and service_metrics to opspilot_app.
"""
import sys
sys.path.insert(0, r"c:\OpsPilot\backend")

from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg://123:123@localhost:5432/opspilot",
    echo=False,
    isolation_level="AUTOCOMMIT",
)

grants = [
    "GRANT SELECT, INSERT, UPDATE, DELETE ON core.app_logs TO opspilot_app",
    "GRANT SELECT, INSERT, UPDATE, DELETE ON core.service_metrics TO opspilot_app",
    "GRANT USAGE, SELECT ON SEQUENCE core.app_logs_log_id_seq TO opspilot_app",
    "GRANT USAGE, SELECT ON SEQUENCE core.service_metrics_metric_id_seq TO opspilot_app",
]

with engine.connect() as conn:
    for stmt in grants:
        try:
            conn.execute(text(stmt))
            print(f"OK: {stmt}")
        except Exception as e:
            print(f"WARN: {e}")

print("Done.")
