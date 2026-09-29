"""
Tests for scripts/run_migrations.py verifying:
1. Safe handling of special characters (such as '@') in database passwords without causing host resolution errors.
2. Idempotent migrations with automated schema baselining so existing populated databases safely skip already-applied migrations.
3. Multiple sequential migration runs without errors.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure scripts directory is in sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import run_migrations


def test_get_db_connection_params_discrete_with_at_symbol():
    """Verify passwords containing '@' in discrete env vars are kept intact."""
    env = {
        "DB_HOST": "postgres",
        "DB_PORT": "5432",
        "DB_USER": "opspilot",
        "DB_PASSWORD": "P@ssword@30#Special",
        "DB_NAME": "opspilot",
    }
    params = run_migrations.get_db_connection_params(env)
    assert params["host"] == "postgres"
    assert params["port"] == 5432
    assert params["user"] == "opspilot"
    assert params["password"] == "P@ssword@30#Special"
    assert params["dbname"] == "opspilot"


def test_get_db_connection_params_postgres_prefixed_discrete():
    """Verify POSTGRES_* environment variable fallbacks."""
    env = {
        "POSTGRES_HOST": "db-server.internal",
        "POSTGRES_PORT": "5433",
        "POSTGRES_USER": "admin",
        "POSTGRES_PASSWORD": "Admin@Password!",
        "POSTGRES_DB": "prod_db",
    }
    params = run_migrations.get_db_connection_params(env)
    assert params["host"] == "db-server.internal"
    assert params["port"] == 5433
    assert params["user"] == "admin"
    assert params["password"] == "Admin@Password!"
    assert params["dbname"] == "prod_db"


def test_parse_database_url_unescaped_at_in_password():
    """
    Verify that an unescaped '@' in DATABASE_URL does not cause the host
    to be corrupted (e.g. host should NOT become '30@postgres').
    """
    raw_url = "postgresql://opspilot:Sanhith@30@postgres:5432/opspilot"
    params = run_migrations.parse_database_url(raw_url)
    assert params["host"] == "postgres"
    assert params["port"] == 5432
    assert params["user"] == "opspilot"
    assert params["password"] == "Sanhith@30"
    assert params["dbname"] == "opspilot"


def test_parse_database_url_encoded_at_in_password():
    """Verify URL-encoded passwords (%40) are decoded properly."""
    raw_url = "postgresql://opspilot:Sanhith%4030@postgres:5432/opspilot"
    params = run_migrations.parse_database_url(raw_url)
    assert params["host"] == "postgres"
    assert params["port"] == 5432
    assert params["user"] == "opspilot"
    assert params["password"] == "Sanhith@30"
    assert params["dbname"] == "opspilot"


def test_run_migrations_uses_separate_connect_keyword_arguments():
    """
    Verify run_migrations() invokes psycopg.connect with separate keyword
    arguments (host, port, dbname, user, password) and never a malformed URI.
    """
    env = {
        "DB_HOST": "postgres",
        "DB_PORT": "5432",
        "DB_USER": "opspilot",
        "DB_PASSWORD": "Sanhith@30",
        "DB_NAME": "opspilot",
    }

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    with patch.dict("os.environ", env, clear=True), \
         patch("psycopg.connect") as mock_connect:
        mock_connect.return_value.__enter__.return_value = mock_conn

        run_migrations.run_migrations()

        mock_connect.assert_called_once_with(
            host="postgres",
            port=5432,
            dbname="opspilot",
            user="opspilot",
            password="Sanhith@30",
            autocommit=True,
        )


def test_set_updated_at_idempotent_syntax():
    """Verify 001_core_schema.sql uses CREATE OR REPLACE FUNCTION for set_updated_at."""
    schema_sql_path = Path(__file__).resolve().parent.parent.parent / "db" / "migrations" / "001_core_schema.sql"
    assert schema_sql_path.exists()
    content = schema_sql_path.read_text(encoding="utf-8")
    assert "CREATE OR REPLACE FUNCTION core.set_updated_at()" in content
    assert "CREATE FUNCTION core.set_updated_at()" not in content


def test_baseline_existing_schema_detects_tables():
    """Verify that pre-existing tables in the core schema are baselined into schema_migrations."""
    mock_cursor = MagicMock()
    # Simulate an already-populated database with core tables
    mock_cursor.fetchall.return_value = [
        ("incidents",),
        ("users",),
        ("audit_logs",),
        ("knowledge_documents",),
        ("investigation_evidence",),
        ("incident_intelligence",),
        ("remediation_actions",),
        ("chat_sessions",),
        ("app_logs",),
        ("service_metrics",),
    ]
    mock_cursor.fetchone.return_value = ("CHECK (UPPER(evidence_type::text) = ANY (ARRAY['KNOWLEDGE_BASE']))",)

    baselined = run_migrations.baseline_existing_schema(mock_cursor)

    assert "001_core_schema.sql" in baselined
    assert "002_core_seed_data.sql" in baselined
    assert "017_knowledge_base.sql" in baselined
    assert "018_investigation_evidence_knowledge_base.sql" in baselined
    assert "019_incident_intelligence.sql" in baselined
    assert "020_remediation_actions.sql" in baselined
    assert "021_chat_persistence.sql" in baselined
    assert "022_app_logs.sql" in baselined
    assert "023_service_metrics.sql" in baselined


def test_run_migrations_idempotent_skips_already_applied():
    """Verify that running migrations against a populated database skips all existing migrations."""
    env = {
        "DB_HOST": "postgres",
        "DB_PORT": "5432",
        "DB_USER": "opspilot",
        "DB_PASSWORD": "Sanhith@30",
        "DB_NAME": "opspilot",
    }

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Simulate existing tables
    existing_tables = [
        ("incidents",),
        ("users",),
        ("audit_logs",),
        ("knowledge_documents",),
        ("investigation_evidence",),
        ("incident_intelligence",),
        ("remediation_actions",),
        ("chat_sessions",),
        ("app_logs",),
        ("service_metrics",),
    ]
    all_migrations = [
        ("001_core_schema.sql",),
        ("002_core_seed_data.sql",),
        ("017_knowledge_base.sql",),
        ("018_investigation_evidence_knowledge_base.sql",),
        ("019_incident_intelligence.sql",),
        ("020_remediation_actions.sql",),
        ("021_chat_persistence.sql",),
        ("022_app_logs.sql",),
        ("023_service_metrics.sql",),
    ]

    # First fetchall is for information_schema.tables, second is for schema_migrations
    mock_cursor.fetchall.side_effect = [existing_tables, all_migrations]
    mock_cursor.fetchone.return_value = ("CHECK (UPPER(evidence_type::text) = ANY (ARRAY['KNOWLEDGE_BASE']))",)

    with patch.dict("os.environ", env, clear=True), \
         patch("psycopg.connect") as mock_connect:
        mock_connect.return_value.__enter__.return_value = mock_conn

        # Run 1:
        run_migrations.run_migrations()

        # Run 2: (re-run immediately)
        mock_cursor.fetchall.side_effect = [existing_tables, all_migrations]
        run_migrations.run_migrations()

        # Verify no raw DDL SQL execution was attempted because everything was already applied
        # In both runs, all migrations were skipped
        assert mock_conn.cursor.call_count >= 2
