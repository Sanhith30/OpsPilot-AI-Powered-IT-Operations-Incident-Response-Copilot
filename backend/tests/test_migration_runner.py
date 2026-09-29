"""
Tests for scripts/run_migrations.py verifying safe handling of special characters
(such as '@') in database passwords without causing host resolution errors.
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
