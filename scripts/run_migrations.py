#!/usr/bin/env python3
"""
OpsPilot Production Database Migration Runner
Applies sequential SQL migrations from db/migrations/ in an idempotent,
audited manner using psycopg directly.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg


def _to_psycopg_conninfo(database_url: str) -> str:
    """
    Convert a DATABASE_URL to a psycopg conninfo string.

    Accepts either:
      - postgresql+psycopg://user:pass@host:port/db  (SQLAlchemy format from CI)
      - postgresql://user:pass@host:port/db
      - postgres://user:pass@host:port/db
      - An already-valid psycopg conninfo / DSN string
    """
    for prefix in (
        "postgresql+psycopg://",
        "postgresql://",
        "postgres://",
    ):
        if database_url.startswith(prefix):
            return "postgresql://" + database_url[len(prefix):]
    # Already a raw conninfo string — return as-is
    return database_url


def run_migrations() -> None:
    raw_url = os.environ.get("DATABASE_URL")
    if not raw_url:
        print("[-] Error: DATABASE_URL environment variable is required.")
        sys.exit(1)

    conninfo = _to_psycopg_conninfo(raw_url)

    migrations_dir = Path(__file__).resolve().parent.parent / "db" / "migrations"
    if not migrations_dir.exists():
        print(f"[-] Migrations directory not found at: {migrations_dir}")
        sys.exit(1)

    migration_files = sorted(migrations_dir.glob("*.sql"), key=lambda p: p.name)
    print(f"[*] Found {len(migration_files)} migration file(s) in {migrations_dir}")

    print("[*] Connecting to database...")
    with psycopg.connect(conninfo, autocommit=True) as conn:
        with conn.cursor() as cur:
            # Ensure tracking schema and table exist
            try:
                cur.execute("CREATE SCHEMA IF NOT EXISTS core;")
            except Exception:
                pass  # non-superuser may lack CREATE SCHEMA — schema already exists
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS core.schema_migrations (
                    migration_name VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                "SELECT migration_name FROM core.schema_migrations ORDER BY migration_name;"
            )
            already_applied = {row[0] for row in cur.fetchall()}

        for sql_file in migration_files:
            migration_name = sql_file.name

            if migration_name in already_applied:
                print(f"[~] Skipping (already applied): {migration_name}")
                continue

            print(f"[+] Applying migration: {migration_name} ...")
            sql_content = sql_file.read_text(encoding="utf-8")

            try:
                with conn.cursor() as cur:
                    cur.execute(sql_content)
                    cur.execute(
                        """
                        INSERT INTO core.schema_migrations (migration_name)
                        VALUES (%s)
                        ON CONFLICT DO NOTHING;
                        """,
                        (migration_name,),
                    )
                print(f"[+] Successfully applied: {migration_name}")
            except Exception as exc:
                print(f"[-] Migration failed on {migration_name}: {exc}")
                sys.exit(1)

    print("[+] All migrations are up to date!")


if __name__ == "__main__":
    run_migrations()
