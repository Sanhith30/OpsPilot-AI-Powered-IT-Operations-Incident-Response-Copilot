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
                    VALUES (%s);
                    """,
                    (migration_name,),
                )

            applied.append(migration_name)
            logger.info("Successfully applied migration: %s", migration_name)

    return applied
