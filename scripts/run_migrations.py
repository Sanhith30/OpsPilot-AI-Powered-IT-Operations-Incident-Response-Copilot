#!/usr/bin/env python3
"""
OpsPilot Production Database Migration Runner
Applies sequential SQL migrations from db/migrations/ in an idempotent, audited manner.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text


def run_migrations():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("[-] Error: DATABASE_URL environment variable is required.")
        sys.exit(1)

    print("[*] Connecting to database...")
    engine = create_engine(db_url, isolation_level="AUTOCOMMIT")

    migrations_dir = Path(__file__).resolve().parent.parent / "db" / "migrations"
    if not migrations_dir.exists():
        print(f"[-] Migrations directory not found at: {migrations_dir}")
        sys.exit(1)

    migration_files = sorted(list(migrations_dir.glob("*.sql")))
    print(f"[*] Found {len(migration_files)} migration files in {migrations_dir}")

    with engine.connect() as conn:
        # Create schema migrations table if not exists
        conn.execute(text("""
            CREATE SCHEMA IF NOT EXISTS core;
            CREATE TABLE IF NOT EXISTS core.schema_migrations (
                version VARCHAR(100) PRIMARY KEY,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))

        for sql_file in migration_files:
            version = sql_file.name
            already_applied = conn.execute(
                text("SELECT 1 FROM core.schema_migrations WHERE version = :version"),
                {"version": version}
            ).scalar_one_or_none()

            if already_applied:
                print(f"[~] Skipping already applied migration: {version}")
                continue

            print(f"[+] Applying migration: {version}...")
            content = sql_file.read_text(encoding="utf-8")
            try:
                conn.execute(text(content))
                conn.execute(
                    text("INSERT INTO core.schema_migrations (version) VALUES (:version)"),
                    {"version": version}
                )
                print(f"[+] Successfully applied: {version}")
            except Exception as exc:
                print(f"[-] Migration failed on {version}: {exc}")
                sys.exit(1)

    print("[+] All migrations up to date!")


if __name__ == "__main__":
    run_migrations()
