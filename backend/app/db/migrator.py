from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import psycopg

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "db" / "migrations"


def get_migration_files(migrations_dir: Path | None = None) -> list[Path]:
    """Find all .sql migration files in ascending numeric order."""
    if migrations_dir is None:
        migrations_dir = MIGRATIONS_DIR
        # Fallback to backend/db/migrations if db/migrations not found
        if not migrations_dir.exists():
            migrations_dir = (
                Path(__file__).resolve().parent.parent / "db" / "migrations"
            )

    if not migrations_dir.exists():
        raise FileNotFoundError(
            f"Migrations directory not found: {migrations_dir}"
        )

    files = sorted(
        migrations_dir.glob("*.sql"),
        key=lambda p: p.name,
    )
    return files


def baseline_existing_schema(cur: Any) -> set[str]:
    """
    Detect tables that already exist in the database from prior initializations
    and register their corresponding migrations in core.schema_migrations so they are safely skipped.
    """
    cur.execute(
        """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'core';
        """
    )
    existing_tables = {row[0] for row in cur.fetchall()}
    baselined: set[str] = set()

    if "incidents" in existing_tables or "users" in existing_tables or "audit_logs" in existing_tables:
        baselined.add("001_core_schema.sql")
        baselined.add("002_core_seed_data.sql")

    if "knowledge_documents" in existing_tables:
        baselined.add("017_knowledge_base.sql")

    if "investigation_evidence" in existing_tables:
        try:
            cur.execute(
                """
                SELECT pg_get_constraintdef(c.oid)
                FROM pg_constraint c
                JOIN pg_namespace n ON n.oid = c.connamespace
                WHERE n.nspname = 'core' AND c.conname = 'ck_investigation_evidence_type';
                """
            )
            row = cur.fetchone()
            if row and "KNOWLEDGE_BASE" in str(row[0]):
                baselined.add("018_investigation_evidence_knowledge_base.sql")
        except Exception:
            pass

    if "incident_intelligence" in existing_tables:
        baselined.add("019_incident_intelligence.sql")

    if "remediation_actions" in existing_tables:
        baselined.add("020_remediation_actions.sql")

    if "chat_sessions" in existing_tables:
        baselined.add("021_chat_persistence.sql")

    if "app_logs" in existing_tables:
        baselined.add("022_app_logs.sql")

    if "service_metrics" in existing_tables:
        baselined.add("023_service_metrics.sql")

    for migration_name in sorted(baselined):
        cur.execute(
            """
            INSERT INTO core.schema_migrations (migration_name)
            VALUES (%s)
            ON CONFLICT (migration_name) DO NOTHING;
            """,
            (migration_name,),
        )

    return baselined


def run_migrations(
    *,
    conn_params: dict[str, Any] | str,
    migrations_dir: Path | None = None,
) -> list[str]:
    """Execute all pending migrations against the target PostgreSQL database."""
    files = get_migration_files(migrations_dir)
    applied: list[str] = []

    conn_args = (
        conn_params if isinstance(conn_params, dict) else {"conninfo": conn_params}
    )

    with psycopg.connect(**conn_args, autocommit=True) as conn:
        with conn.cursor() as cur:
            # Ensure core schema exists for tracking table (ignore if already exists or non-superuser)
            try:
                cur.execute("CREATE SCHEMA IF NOT EXISTS core;")
            except Exception:
                pass
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS core.schema_migrations (
                    migration_name VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                );
                """
            )
            # Baseline any pre-existing database tables
            baseline_existing_schema(cur)

            cur.execute(
                "SELECT migration_name FROM core.schema_migrations ORDER BY migration_name;"
            )
            already_applied = {row[0] for row in cur.fetchall()}

        for file_path in files:
            migration_name = file_path.name
            if migration_name in already_applied:
                logger.info("Skipping already applied migration: %s", migration_name)
                continue

            logger.info("Applying migration: %s", migration_name)
            sql_content = file_path.read_text(encoding="utf-8")

            # Execute migration in a single transaction block
            with conn.cursor() as cur:
                cur.execute(sql_content)
                cur.execute(
                    """
                    INSERT INTO core.schema_migrations (migration_name)
                    VALUES (%s)
                    ON CONFLICT (migration_name) DO NOTHING;
                    """,
                    (migration_name,),
                )

            applied.append(migration_name)
            logger.info("Successfully applied migration: %s", migration_name)

    return applied
