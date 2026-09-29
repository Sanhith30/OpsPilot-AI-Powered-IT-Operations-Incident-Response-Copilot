BEGIN;

CREATE TABLE IF NOT EXISTS core.incident_intelligence (
    intelligence_id BIGSERIAL PRIMARY KEY,
    incident_id BIGINT NOT NULL REFERENCES core.incidents(incident_id) ON DELETE CASCADE,
    investigation_id BIGINT NOT NULL REFERENCES core.investigations(investigation_id) ON DELETE CASCADE,
    incident_summary TEXT NOT NULL,
    correlated_signals JSONB NOT NULL DEFAULT '[]'::jsonb,
    probable_root_causes JSONB NOT NULL DEFAULT '[]'::jsonb,
    impact_assessment JSONB NOT NULL DEFAULT '{}'::jsonb,
    risk_assessment JSONB NOT NULL DEFAULT '{}'::jsonb,
    recommended_actions JSONB NOT NULL DEFAULT '[]'::jsonb,
    operational_decision JSONB NOT NULL DEFAULT '{}'::jsonb,
    overall_confidence NUMERIC(5, 4) NOT NULL,
    model_name VARCHAR(150),
    model_version VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_incident_intelligence_incident
    ON core.incident_intelligence(incident_id);

CREATE INDEX IF NOT EXISTS idx_incident_intelligence_investigation
    ON core.incident_intelligence(investigation_id);

CREATE INDEX IF NOT EXISTS idx_incident_intelligence_created_at
    ON core.incident_intelligence(created_at);

GRANT SELECT, INSERT, UPDATE ON core.incident_intelligence TO opspilot_app;
GRANT SELECT ON core.incident_intelligence TO opspilot_agent_ro;

GRANT USAGE, SELECT ON SEQUENCE core.incident_intelligence_intelligence_id_seq TO opspilot_app;

COMMIT;
