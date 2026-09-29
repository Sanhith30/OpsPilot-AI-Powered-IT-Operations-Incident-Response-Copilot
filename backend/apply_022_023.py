"""
Apply migrations 022 and 023 using SQLAlchemy (no raw psycopg2 needed).
"""
import os
import sys

# Add backend to path so app config is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://123:123@localhost:5432/opspilot"
)

migration_files = [
    "db/migrations/022_app_logs.sql",
    "db/migrations/023_service_metrics.sql",
]

engine = create_engine(DATABASE_URL, echo=False, isolation_level="AUTOCOMMIT")

with engine.connect() as conn:
    for mig_file in migration_files:
        print(f"\nApplying {mig_file}...")
        with open(mig_file, "r", encoding="utf-8") as f:
            sql = f.read()
        try:
            conn.execute(text(sql))
            print(f"  OK: Applied successfully.")
        except Exception as e:
            print(f"  WARN: Error (may already exist): {e}")

print("\nDone.")
