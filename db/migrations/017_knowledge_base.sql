BEGIN;

CREATE TABLE IF NOT EXISTS core.knowledge_documents (
    document_id BIGSERIAL PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    owner_team_id BIGINT REFERENCES core.teams(team_id) ON DELETE SET NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    current_version_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_knowledge_documents_source UNIQUE (source_type, source_name),
    CONSTRAINT ck_knowledge_documents_status CHECK (
        
        status IN (
            'ACTIVE',
            'ARCHIVED',
            'DISABLED'
        )
    )
);

CREATE TABLE IF NOT EXISTS core.knowledge_document_versions (
    version_id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES core.knowledge_documents(document_id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    content TEXT NOT NULL,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    embedding_model VARCHAR(100),
    embedding_dimensions INTEGER,
    ingestion_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    ingestion_error TEXT,
    created_by BIGINT REFERENCES core.users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_knowledge_document_version UNIQUE (document_id, version_number),
    CONSTRAINT uq_knowledge_document_content_hash UNIQUE (document_id, content_hash),
    CONSTRAINT ck_knowledge_document_version_number CHECK (version_number > 0),
    CONSTRAINT ck_knowledge_document_chunk_count CHECK (chunk_count >= 0),
    CONSTRAINT ck_knowledge_document_ingestion_status CHECK (
        ingestion_status IN (
            'PENDING',
            'PROCESSING',
            'COMPLETED',
            'FAILED'
        )
    )
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_knowledge_documents_current_version'
    ) THEN
        ALTER TABLE core.knowledge_documents
            ADD CONSTRAINT fk_knowledge_documents_current_version
            FOREIGN KEY (current_version_id)
            REFERENCES core.knowledge_document_versions(version_id)
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_knowledge_documents_status
    ON core.knowledge_documents(status);

CREATE INDEX IF NOT EXISTS idx_knowledge_documents_owner_team
    ON core.knowledge_documents(owner_team_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_document_versions_document
    ON core.knowledge_document_versions(document_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_document_versions_hash
    ON core.knowledge_document_versions(content_hash);

CREATE INDEX IF NOT EXISTS idx_knowledge_document_versions_status
    ON core.knowledge_document_versions(ingestion_status);

GRANT SELECT, INSERT, UPDATE ON core.knowledge_documents TO opspilot_app;
GRANT SELECT, INSERT, UPDATE ON core.knowledge_document_versions TO opspilot_app;

GRANT SELECT ON core.knowledge_documents, core.knowledge_document_versions TO opspilot_agent_ro;

GRANT USAGE, SELECT ON SEQUENCE core.knowledge_documents_document_id_seq TO opspilot_app;
GRANT USAGE, SELECT ON SEQUENCE core.knowledge_document_versions_version_id_seq TO opspilot_app;

COMMIT;
