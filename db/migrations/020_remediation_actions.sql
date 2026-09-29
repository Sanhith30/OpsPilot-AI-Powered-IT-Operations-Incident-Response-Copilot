BEGIN;

CREATE TABLE IF NOT EXISTS core.remediation_actions (
    remediation_id BIGSERIAL PRIMARY KEY,
    incident_id BIGINT NOT NULL REFERENCES core.incidents(incident_id) ON DELETE CASCADE,
    investigation_id BIGINT REFERENCES core.investigations(investigation_id) ON DELETE SET NULL,
    intelligence_id BIGINT REFERENCES core.incident_intelligence(intelligence_id) ON DELETE SET NULL,
    action_id VARCHAR(50) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    rationale TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING_APPROVAL',
    execution_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    requested_by_user_id BIGINT NOT NULL REFERENCES core.users(user_id) ON DELETE RESTRICT,
    approved_by_user_id BIGINT REFERENCES core.users(user_id) ON DELETE SET NULL,
    approved_at TIMESTAMP WITH TIME ZONE,
    review_comment TEXT,
    execution_result JSONB NOT NULL DEFAULT '{}'::jsonb,
    execution_started_at TIMESTAMP WITH TIME ZONE,
    execution_completed_at TIMESTAMP WITH TIME ZONE,
    verification_status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    verification_result JSONB NOT NULL DEFAULT '{}'::jsonb,
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_remediation_incident
    ON core.remediation_actions(incident_id);

CREATE INDEX IF NOT EXISTS idx_remediation_investigation
    ON core.remediation_actions(investigation_id);

CREATE INDEX IF NOT EXISTS idx_remediation_status
    ON core.remediation_actions(status);

CREATE INDEX IF NOT EXISTS idx_remediation_created_at
    ON core.remediation_actions(created_at);

GRANT SELECT, INSERT, UPDATE, DELETE ON core.remediation_actions TO opspilot_app;
GRANT SELECT ON core.remediation_actions TO opspilot_agent_ro;

GRANT USAGE, SELECT ON SEQUENCE core.remediation_actions_remediation_id_seq TO opspilot_app;

COMMIT;
