#!/usr/bin/env python3
"""
OpsPilot Production Database Migration Runner
Applies sequential SQL migrations from db/migrations/ in an idempotent,
audited manner using psycopg directly with separate connection arguments.
"""

from __future__ import annotations

import os
import sys
import urllib.parse
from pathlib import Path
from typing import Any

import psycopg


def parse_database_url(url: str) -> dict[str, Any]:
    """
    Parse a PostgreSQL database URL into separate connection parameters.
    Handles unescaped or escaped '@' in passwords safely by recognizing that host
    names and ports cannot contain '@', splitting userinfo and hostinfo from the right.
    """
    cleaned_url = url
    for prefix in ("postgresql+psycopg://", "postgresql://", "postgres://"):
        if cleaned_url.startswith(prefix):
            cleaned_url = cleaned_url[len(prefix):]
            break

    # Extract query params if any
    if "?" in cleaned_url:
        cleaned_url, _ = cleaned_url.split("?", 1)

    # Separate dbname from user:pass@host:port
    remainder, sep, dbname = cleaned_url.rpartition("/")
    if not sep:
        remainder = dbname
        dbname = "opspilot"

    # Separate userinfo from hostinfo using rsplit on '@' from the right
    user = "postgres"
    password = ""
    if "@" in remainder:
        userinfo, hostinfo = remainder.rsplit("@", 1)
        if ":" in userinfo:
            user, password = userinfo.split(":", 1)
            password = urllib.parse.unquote(password)
        else:
            user = urllib.parse.unquote(userinfo)
    else:
        hostinfo = remainder

    # Extract host and port
    if ":" in hostinfo:
        host, port_str = hostinfo.split(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            port = 5432
    else:
        host = hostinfo or "127.0.0.1"
        port = 5432

    return {
        "host": host,
        "port": port,
        "dbname": dbname or "opspilot",
        "user": user,
        "password": password,
    }


def get_db_connection_params(env: dict[str, str] | None = None) -> dict[str, Any]:
    """
    Resolve PostgreSQL connection parameters from environment variables as separate
    keyword arguments (host, port, dbname, user, password) to avoid URI parsing issues
    when credentials contain special characters such as '@'.
    """
    if env is None:
        env = dict(os.environ)

    # Check discrete environment variables first
    db_user = env.get("DB_USER") or env.get("POSTGRES_USER")
    db_pass = env.get("DB_PASSWORD") or env.get("POSTGRES_PASSWORD")
    db_host = env.get("DB_HOST") or env.get("POSTGRES_HOST")
    db_port = env.get("DB_PORT") or env.get("POSTGRES_PORT")
    db_name = env.get("DB_NAME") or env.get("POSTGRES_DB")

    raw_url = env.get("DATABASE_URL") or env.get("DB_URL")

    # If discrete host or credentials are provided, return keyword arguments directly
    if db_host or (db_user and db_pass):
        return {
            "host": db_host or "127.0.0.1",
            "port": int(db_port) if db_port else 5432,
            "dbname": db_name or "opspilot",
            "user": db_user or "postgres",
            "password": db_pass or "",
        }

    # If only DATABASE_URL / DB_URL is provided, safely parse components
    if raw_url:
        return parse_database_url(raw_url)

    # Default fallback
    return {
        "host": db_host or "127.0.0.1",
        "port": int(db_port) if db_port else 5432,
        "dbname": db_name or "opspilot",
        "user": db_user or "postgres",
        "password": db_pass or "",
    }


def run_migrations(migrations_dir: Path | None = None) -> None:
    conn_params = get_db_connection_params()

    if migrations_dir is None:
        migrations_dir = Path(__file__).resolve().parent.parent / "db" / "migrations"

    if not migrations_dir.exists():
        alt_dir = Path("/app/db/migrations")
        if alt_dir.exists():
            migrations_dir = alt_dir
        else:
            print(f"[-] Migrations directory not found at: {migrations_dir}")
            sys.exit(1)

    migration_files = sorted(migrations_dir.glob("*.sql"), key=lambda p: p.name)
    print(f"[*] Found {len(migration_files)} migration file(s) in {migrations_dir}")

    host = conn_params["host"]
    port = conn_params["port"]
    dbname = conn_params["dbname"]
    user = conn_params["user"]
    password = conn_params.get("password", "")

    print(f"[*] Connecting to database at {host}:{port}/{dbname} as user '{user}'...")

    with psycopg.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        autocommit=True,
    ) as conn:
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
