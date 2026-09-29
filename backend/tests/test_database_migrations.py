from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
import pytest

from app.db.migrator import get_migration_files


def test_migration_files_order():
    files = get_migration_files()
    filenames = [f.name for f in files]
    assert "001_core_schema.sql" in filenames
    assert "002_core_seed_data.sql" in filenames
    assert "017_knowledge_base.sql" in filenames
    assert "018_investigation_evidence_knowledge_base.sql" in filenames
    assert "019_incident_intelligence.sql" in filenames
    assert "020_remediation_actions.sql" in filenames
    assert "021_chat_persistence.sql" in filenames

    # Verify strictly sorted order
    assert filenames == sorted(filenames)


def test_remediation_actions_table_exists(db_session):
    inspector = inspect(db_session.connection())
    tables = inspector.get_table_names(schema="core")
    assert "remediation_actions" in tables

    columns = {
        col["name"]: col
        for col in inspector.get_columns("remediation_actions", schema="core")
    }
    expected_cols = [
        "remediation_id",
        "incident_id",
        "investigation_id",
        "intelligence_id",
        "action_id",
        "action_type",
        "title",
        "description",
        "rationale",
        "status",
        "execution_payload",
        "requested_by_user_id",
        "approved_by_user_id",
        "approved_at",
        "review_comment",
        "execution_result",
        "execution_started_at",
        "execution_completed_at",
        "verification_status",
        "verification_result",
        "verified_at",
        "created_at",
        "updated_at",
    ]
    for col_name in expected_cols:
        assert col_name in columns, f"Missing column: {col_name}"


def test_incident_intelligence_table_exists(db_session):
    inspector = inspect(db_session.connection())
    tables = inspector.get_table_names(schema="core")
    assert "incident_intelligence" in tables

    columns = {
        col["name"]: col
        for col in inspector.get_columns("incident_intelligence", schema="core")
    }
    expected_cols = [
        "intelligence_id",
        "incident_id",
        "investigation_id",
        "incident_summary",
        "correlated_signals",
        "probable_root_causes",
        "impact_assessment",
        "risk_assessment",
        "recommended_actions",
        "operational_decision",
        "overall_confidence",
        "model_name",
        "model_version",
        "created_at",
    ]
    for col_name in expected_cols:
        assert col_name in columns, f"Missing column: {col_name}"


def test_knowledge_documents_table_exists(db_session):
    inspector = inspect(db_session.connection())
    tables = inspector.get_table_names(schema="core")
    assert "knowledge_documents" in tables

    columns = {
        col["name"]: col
        for col in inspector.get_columns("knowledge_documents", schema="core")
    }
    expected_cols = [
        "document_id",
        "source_type",
        "source_name",
        "title",
        "description",
        "owner_team_id",
        "status",
        "current_version_id",
        "created_at",
        "updated_at",
    ]
    for col_name in expected_cols:
        assert col_name in columns, f"Missing column: {col_name}"


def test_knowledge_document_versions_table_exists(db_session):
    inspector = inspect(db_session.connection())
    tables = inspector.get_table_names(schema="core")
    assert "knowledge_document_versions" in tables

    columns = {
        col["name"]: col
        for col in inspector.get_columns(
            "knowledge_document_versions", schema="core"
        )
    }
    expected_cols = [
        "version_id",
        "document_id",
        "version_number",
        "content_hash",
        "content",
        "chunk_count",
        "embedding_model",
        "embedding_dimensions",
        "ingestion_status",
        "ingestion_error",
        "created_by",
        "created_at",
    ]
    for col_name in expected_cols:
        assert col_name in columns, f"Missing column: {col_name}"


def test_knowledge_base_evidence_type_allowed(db_session):
    # Check constraint definition in PostgreSQL
    result = db_session.execute(
        text(
            """
            SELECT conname, pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conname = 'ck_investigation_evidence_type';
            """
        )
    ).fetchone()

    assert result is not None
    assert "KNOWLEDGE_BASE" in result[1]

    # Test inserting KNOWLEDGE_BASE succeeds
    insert_res = db_session.execute(
        text(
            """
            INSERT INTO core.investigation_evidence (
                investigation_id, evidence_type, source_name, evidence_text
            ) VALUES (1, 'KNOWLEDGE_BASE', 'migration_test.md', 'Valid knowledge text')
            RETURNING evidence_id;
            """
        )
    )
    eid = insert_res.scalar()
    assert eid is not None

    # Test invalid evidence type is rejected
    with pytest.raises(IntegrityError):
        db_session.execute(
            text(
                """
                INSERT INTO core.investigation_evidence (
                    investigation_id, evidence_type, source_name, evidence_text
                ) VALUES (1, 'UNSUPPORTED_TYPE_XYZ', 'bad.md', 'Invalid text')
                RETURNING evidence_id;
                """
            )
        )
    db_session.rollback()


def test_current_version_foreign_key_exists(db_session):
    result = db_session.execute(
        text(
            """
            SELECT conname, pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conname = 'fk_knowledge_documents_current_version';
            """
        )
    ).fetchone()

    assert result is not None
    assert "FOREIGN KEY (current_version_id)" in result[1]
    assert "REFERENCES core.knowledge_document_versions(version_id)" in result[1]
    assert "ON DELETE SET NULL" in result[1]


def test_version_uniqueness_exists(db_session):
    result = db_session.execute(
        text(
            """
            SELECT conname, pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conname = 'uq_knowledge_document_version';
            """
        )
    ).fetchone()

    assert result is not None
    assert "UNIQUE (document_id, version_number)" in result[1]

    # Verify enforcement
    doc_res = db_session.execute(
        text(
            """
            INSERT INTO core.knowledge_documents (source_type, source_name, title)
            VALUES ('DOC', 'uq_test_1.md', 'UQ Test')
            RETURNING document_id;
            """
        )
    )
    doc_id = doc_res.scalar()

    db_session.execute(
        text(
            """
            INSERT INTO core.knowledge_document_versions (
                document_id, version_number, content_hash, content, chunk_count, ingestion_status
            ) VALUES (:doc_id, 1, 'hash_1a', 'Content 1', 1, 'COMPLETED');
            """
        ),
        {"doc_id": doc_id},
    )

    with pytest.raises(IntegrityError):
        db_session.execute(
            text(
                """
                INSERT INTO core.knowledge_document_versions (
                    document_id, version_number, content_hash, content, chunk_count, ingestion_status
                ) VALUES (:doc_id, 1, 'hash_1b', 'Content Duplicate Version', 1, 'COMPLETED');
                """
            ),
            {"doc_id": doc_id},
        )
    db_session.rollback()


def test_content_hash_uniqueness_exists(db_session):
    result = db_session.execute(
        text(
            """
            SELECT conname, pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conname = 'uq_knowledge_document_content_hash';
            """
        )
    ).fetchone()

    assert result is not None
    assert "UNIQUE (document_id, content_hash)" in result[1]

    doc_res = db_session.execute(
        text(
            """
            INSERT INTO core.knowledge_documents (source_type, source_name, title)
            VALUES ('DOC', 'hash_test_1.md', 'Hash Test')
            RETURNING document_id;
            """
        )
    )
    doc_id = doc_res.scalar()

    db_session.execute(
        text(
            """
            INSERT INTO core.knowledge_document_versions (
                document_id, version_number, content_hash, content, chunk_count, ingestion_status
            ) VALUES (:doc_id, 1, 'duplicate_hash', 'Content 1', 1, 'COMPLETED');
            """
        ),
        {"doc_id": doc_id},
    )

    with pytest.raises(IntegrityError):
        db_session.execute(
            text(
                """
                INSERT INTO core.knowledge_document_versions (
                    document_id, version_number, content_hash, content, chunk_count, ingestion_status
                ) VALUES (:doc_id, 2, 'duplicate_hash', 'Content 2 with same hash', 1, 'COMPLETED');
                """
            ),
            {"doc_id": doc_id},
        )
    db_session.rollback()


def test_indexes_exist(db_session):
    indexes_res = db_session.execute(
        text(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'core'
              AND tablename IN ('knowledge_documents', 'knowledge_document_versions');
            """
        )
    ).fetchall()

    index_names = {r[0] for r in indexes_res}
    expected_indexes = {
        "idx_knowledge_documents_status",
        "idx_knowledge_documents_owner_team",
        "idx_knowledge_document_versions_document",
        "idx_knowledge_document_versions_hash",
        "idx_knowledge_document_versions_status",
    }
    for expected in expected_indexes:
        assert expected in index_names, f"Missing index: {expected}"


def test_role_grants_exist(db_session):
    # Check opspilot_app and opspilot_agent_ro table permissions
    result = db_session.execute(
        text(
            """
            SELECT
                has_table_privilege('opspilot_agent_ro', 'core.knowledge_documents', 'SELECT') as ro_doc_select,
                has_table_privilege('opspilot_agent_ro', 'core.knowledge_documents', 'INSERT') as ro_doc_insert,
                has_table_privilege('opspilot_agent_ro', 'core.knowledge_document_versions', 'SELECT') as ro_ver_select,
                has_table_privilege('opspilot_agent_ro', 'core.knowledge_document_versions', 'INSERT') as ro_ver_insert,
                has_table_privilege('opspilot_app', 'core.knowledge_documents', 'SELECT') as app_doc_select,
                has_table_privilege('opspilot_app', 'core.knowledge_documents', 'INSERT') as app_doc_insert,
                has_table_privilege('opspilot_app', 'core.knowledge_documents', 'UPDATE') as app_doc_update,
                has_table_privilege('opspilot_app', 'core.knowledge_document_versions', 'SELECT') as app_ver_select,
                has_table_privilege('opspilot_app', 'core.knowledge_document_versions', 'INSERT') as app_ver_insert,
                has_table_privilege('opspilot_app', 'core.knowledge_document_versions', 'UPDATE') as app_ver_update,
                has_sequence_privilege('opspilot_app', 'core.knowledge_documents_document_id_seq', 'USAGE') as app_doc_seq,
                has_sequence_privilege('opspilot_app', 'core.knowledge_document_versions_version_id_seq', 'USAGE') as app_ver_seq;
            """
        )
    ).mappings().fetchone()

    # Agent role has SELECT only
    assert result["ro_doc_select"] is True
    assert result["ro_doc_insert"] is False
    assert result["ro_ver_select"] is True
    assert result["ro_ver_insert"] is False

    # App role has SELECT, INSERT, UPDATE, and SEQUENCE USAGE
    assert result["app_doc_select"] is True
    assert result["app_doc_insert"] is True
    assert result["app_doc_update"] is True
    assert result["app_ver_select"] is True
    assert result["app_ver_insert"] is True
    assert result["app_ver_update"] is True
    assert result["app_doc_seq"] is True
    assert result["app_ver_seq"] is True


def test_clean_database_lifecycle_smoke(db_session):
    # 1. Create knowledge document
    doc_res = db_session.execute(
        text(
            """
            INSERT INTO core.knowledge_documents (source_type, source_name, title, status)
            VALUES ('RUNBOOK', 'payment-runbook-smoke.md', 'Payment Runbook Smoke', 'ACTIVE')
            RETURNING document_id;
            """
        )
    )
    doc_id = doc_res.scalar()
    assert doc_id is not None

    # 2. Insert version 1
    v1_res = db_session.execute(
        text(
            """
            INSERT INTO core.knowledge_document_versions (
                document_id, version_number, content_hash, content, chunk_count, ingestion_status
            ) VALUES (:doc_id, 1, 'smoke_hash_v1', 'Content v1', 3, 'COMPLETED')
            RETURNING version_id;
            """
        ),
        {"doc_id": doc_id},
    )
    v1_id = v1_res.scalar()

    # 3. Promote version 1
    db_session.execute(
        text(
            """
            UPDATE core.knowledge_documents
            SET current_version_id = :v1_id
            WHERE document_id = :doc_id;
            """
        ),
        {"v1_id": v1_id, "doc_id": doc_id},
    )

    cur_v1 = db_session.execute(
        text(
            "SELECT current_version_id FROM core.knowledge_documents WHERE document_id = :doc_id;"
        ),
        {"doc_id": doc_id},
    ).scalar()
    assert cur_v1 == v1_id

    # 4. Insert version 2
    v2_res = db_session.execute(
        text(
            """
            INSERT INTO core.knowledge_document_versions (
                document_id, version_number, content_hash, content, chunk_count, ingestion_status
            ) VALUES (:doc_id, 2, 'smoke_hash_v2', 'Content v2 updated', 5, 'COMPLETED')
            RETURNING version_id;
            """
        ),
        {"doc_id": doc_id},
    )
    v2_id = v2_res.scalar()

    # 5. Promote version 2
    db_session.execute(
        text(
            """
            UPDATE core.knowledge_documents
            SET current_version_id = :v2_id
            WHERE document_id = :doc_id;
            """
        ),
        {"v2_id": v2_id, "doc_id": doc_id},
    )

    cur_v2 = db_session.execute(
        text(
            "SELECT current_version_id FROM core.knowledge_documents WHERE document_id = :doc_id;"
        ),
        {"doc_id": doc_id},
    ).scalar()
    assert cur_v2 == v2_id

    # 6. Archive document
    db_session.execute(
        text(
            """
            UPDATE core.knowledge_documents
            SET status = 'ARCHIVED'
            WHERE document_id = :doc_id;
            """
        ),
        {"doc_id": doc_id},
    )

    # 7. Verify both historical versions remain intact
    versions = db_session.execute(
        text(
            """
            SELECT version_id, version_number, content, ingestion_status
            FROM core.knowledge_document_versions
            WHERE document_id = :doc_id
            ORDER BY version_number;
            """
        ),
        {"doc_id": doc_id},
    ).fetchall()

    assert len(versions) == 2
    assert versions[0][1] == 1 and versions[0][2] == "Content v1"
    assert versions[1][1] == 2 and versions[1][2] == "Content v2 updated"

    # 8. Verify archived document is excluded from active retrieval
    active_doc = db_session.execute(
        text(
            """
            SELECT document_id
            FROM core.knowledge_documents
            WHERE status = 'ACTIVE' AND current_version_id IS NOT NULL AND document_id = :doc_id;
            """
        ),
        {"doc_id": doc_id},
    ).scalar()
    assert active_doc is None


def test_chat_sessions_table_exists(db_session):
    inspector = inspect(db_session.connection())
    tables = inspector.get_table_names(schema="core")
    assert "chat_sessions" in tables

    columns = {
        col["name"]: col
        for col in inspector.get_columns("chat_sessions", schema="core")
    }
    expected_cols = [
        "session_id",
        "user_id",
        "incident_id",
        "title",
        "created_at",
        "updated_at",
    ]
    for col_name in expected_cols:
        assert col_name in columns, f"Missing column: {col_name}"


def test_chat_messages_table_exists(db_session):
    inspector = inspect(db_session.connection())
    tables = inspector.get_table_names(schema="core")
    assert "chat_messages" in tables

    columns = {
        col["name"]: col
        for col in inspector.get_columns("chat_messages", schema="core")
    }
    expected_cols = [
        "message_id",
        "session_id",
        "role",
        "content",
        "tool_trace",
        "citations",
        "risk",
        "investigation_id",
        "created_at",
    ]
    for col_name in expected_cols:
        assert col_name in columns, f"Missing column: {col_name}"


def test_app_logs_table_exists(db_session):
    inspector = inspect(db_session.connection())
    tables = inspector.get_table_names(schema="core")
    assert "app_logs" in tables

    columns = {
        col["name"]: col
        for col in inspector.get_columns("app_logs", schema="core")
    }
    expected_cols = [
        "log_id",
        "service_id",
        "service_name",
        "level",
        "message",
        "logger_name",
        "trace_id",
        "span_id",
        "host",
        "environment",
        "extra",
        "logged_at",
    ]
    for col_name in expected_cols:
        assert col_name in columns, f"Missing column: {col_name}"

    # Verify level CHECK constraint allows valid values
    db_session.execute(
        text(
            """
            INSERT INTO core.app_logs (service_name, level, message)
            VALUES ('test-svc', 'ERROR', 'constraint smoke test')
            ON CONFLICT DO NOTHING;
            """
        )
    )


def test_service_metrics_table_exists(db_session):
    inspector = inspect(db_session.connection())
    tables = inspector.get_table_names(schema="core")
    assert "service_metrics" in tables

    columns = {
        col["name"]: col
        for col in inspector.get_columns("service_metrics", schema="core")
    }
    expected_cols = [
        "metric_id",
        "service_id",
        "service_name",
        "instance_id",
        "environment",
        "metric_name",
        "metric_value",
        "unit",
        "dimensions",
        "recorded_at",
    ]
    for col_name in expected_cols:
        assert col_name in columns, f"Missing column: {col_name}"


def test_migration_files_include_022_and_023():
    from app.db.migrator import get_migration_files

    files = get_migration_files()
    filenames = [f.name for f in files]
    assert "022_app_logs.sql" in filenames, "Migration 022_app_logs.sql is missing"
    assert "023_service_metrics.sql" in filenames, "Migration 023_service_metrics.sql is missing"
