import os
import sys
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository
from app.repositories.knowledge_document_version_repository import KnowledgeDocumentVersionRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_log_service import AuditLogService
from app.ai.rag.ingestion.factory import create_knowledge_ingestion_service
from app.services.knowledge_document_service import KnowledgeDocumentService
from app.schemas.knowledge_document import KnowledgeDocumentCreate

DOCUMENTS_TO_INGEST = [
    {
        "source_type": "RUNBOOK",
        "source_name": "runbooks/authentication-service-token-errors.md",
        "file_path": "knowledge/runbooks/authentication-service-token-errors.md",
        "title": "Authentication Service Token Validation and Database Timeout Runbook",
        "description": "Triage and remediation for authentication service token validation errors, auth database timeouts, and Redis session issues",
        "owner_team_id": 1,
    },
    {
        "source_type": "RUNBOOK",
        "source_name": "runbooks/order-service-latency.md",
        "file_path": "knowledge/runbooks/order-service-latency.md",
        "title": "Order Service Checkout Latency and Database Deadlock Runbook",
        "description": "Investigation and mitigation for order service checkout latency, database deadlock contention, and queue delays",
        "owner_team_id": 1,
    },
    {
        "source_type": "RUNBOOK",
        "source_name": "runbooks/redis-cache-failures.md",
        "file_path": "knowledge/runbooks/redis-cache-failures.md",
        "title": "Redis Cache Connection Timeout and Eviction Failure Runbook",
        "description": "Diagnosis and remediation for Redis connection timeouts, maxmemory exhaustion, and sentinel failover",
        "owner_team_id": 2,
    },
    {
        "source_type": "OPERATION",
        "source_name": "operations/postgresql-connection-pool-guide.md",
        "file_path": "knowledge/operations/postgresql-connection-pool-guide.md",
        "title": "PostgreSQL Global Connection Pool and PgBouncer Sizing Guide",
        "description": "Operational standards for PostgreSQL connection pool configuration, pg_stat_activity analysis, and PgBouncer sizing",
        "owner_team_id": 2,
    },
    {
        "source_type": "OPERATION",
        "source_name": "operations/kubernetes-pod-restart-procedure.md",
        "file_path": "knowledge/operations/kubernetes-pod-restart-procedure.md",
        "title": "Kubernetes Pod CrashLoopBackOff and OOMKilled Restart Procedure",
        "description": "Troubleshooting guide for Kubernetes container crash loops, OOMKilled exit code 137, and probe failures",
        "owner_team_id": 5,
    },
    {
        "source_type": "SOP",
        "source_name": "sops/deployment-rollback-sop.md",
        "file_path": "knowledge/sops/deployment-rollback-sop.md",
        "title": "Standard Operating Procedure for Production Deployment Rollbacks",
        "description": "Standard operating procedure governing production deployment rollback criteria, safety checks, and execution",
        "owner_team_id": 5,
    },
    {
        "source_type": "SOP",
        "source_name": "sops/incident-escalation-sop.md",
        "file_path": "knowledge/sops/incident-escalation-sop.md",
        "title": "Standard Operating Procedure for Incident Severity and Escalation Management",
        "description": "Severity classifications, escalation triggers, role definitions, and communication cadences for production incidents",
        "owner_team_id": None,
    },
    {
        "source_type": "SOP",
        "source_name": "sops/security-incident-sop.md",
        "file_path": "knowledge/sops/security-incident-sop.md",
        "title": "Standard Operating Procedure for Security Compromise and Secret Revocation",
        "description": "Mandatory emergency procedure for compromised credentials, leaked secrets, and unauthorized access",
        "owner_team_id": 4,
    },
    {
        "source_type": "POSTMORTEM",
        "source_name": "postmortems/payment-api-2026-09-timeout.md",
        "file_path": "knowledge/postmortems/payment-api-2026-09-timeout.md",
        "title": "Incident Postmortem: Payment API Database Connection Timeout (September 2026)",
        "description": "Formal postmortem report for SEV-1 Payment API database connection timeout incident following deployment v2.8.1",
        "owner_team_id": None,
    },
]


def resolve_file(rel_path: str) -> Path:
    candidates = [
        Path(rel_path),
        Path("..") / rel_path,
        BACKEND_DIR / rel_path,
        BACKEND_DIR.parent / rel_path,
    ]
    for c in candidates:
        if c.exists():
            return c.resolve()
    raise FileNotFoundError(f"Could not find document file: {rel_path}")


def main():
    print("=" * 70)
    print("Multi-Document Knowledge Base Production Ingestion")
    print("=" * 70)

    db = SessionLocal()
    try:
        doc_repo = KnowledgeDocumentRepository(db)
        ver_repo = KnowledgeDocumentVersionRepository(db)
        audit_repo = AuditLogRepository(db)
        user_repo = UserRepository(db)
        audit_service = AuditLogService(db, audit_repo, user_repo)
        ingestion_service = create_knowledge_ingestion_service(
            db=db,
            document_repository=doc_repo,
            version_repository=ver_repo,
        )
        doc_service = KnowledgeDocumentService(
            db=db,
            document_repository=doc_repo,
            version_repository=ver_repo,
            ingestion_service=ingestion_service,
            audit_log_service=audit_service,
        )

        for doc_info in DOCUMENTS_TO_INGEST:
            source_type = doc_info["source_type"]
            source_name = doc_info["source_name"]
            title = doc_info["title"]
            description = doc_info["description"]
            owner_team_id = doc_info["owner_team_id"]
            file_path = resolve_file(doc_info["file_path"])

            print(f"\nProcessing: {title} ({source_name})...")
            content = file_path.read_text(encoding="utf-8")

            existing = doc_repo.get_by_source(source_type=source_type, source_name=source_name)
            if existing is None:
                create_req = KnowledgeDocumentCreate(
                    source_type=source_type,
                    source_name=source_name,
                    title=title,
                    description=description,
                    owner_team_id=owner_team_id,
                )
                doc = doc_service.create_document(create_req, actor_user_id=1)
                print(f"  Created KnowledgeDocument (ID: {doc.document_id})")
            else:
                doc = existing
                print(f"  Existing KnowledgeDocument found (ID: {doc.document_id})")

            ingest_result = doc_service.ingest_document(
                document_id=doc.document_id,
                content=content,
                actor_user_id=1,
            )
            print(f"  Ingestion status: {ingest_result.get('status')} | Version: {ingest_result.get('version_number')} | Chunks: {ingest_result.get('chunk_count')}")

        print("\n" + "=" * 70)
        print("All documents successfully ingested into PostgreSQL & Pinecone.")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    main()
