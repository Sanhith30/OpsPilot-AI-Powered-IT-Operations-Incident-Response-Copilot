BEGIN;

ALTER TABLE core.investigation_evidence DROP CONSTRAINT IF EXISTS ck_investigation_evidence_type;

ALTER TABLE core.investigation_evidence ADD CONSTRAINT ck_investigation_evidence_type CHECK (
    UPPER(evidence_type::text) = ANY (ARRAY[
        'INCIDENT'::text,
        'LOG'::text,
        'METRIC'::text,
        'DEPLOYMENT'::text,
        'RUNBOOK'::text,
        'TICKET'::text,
        'TRACE'::text,
        'ML_PREDICTION'::text,
        'SYSTEM'::text,
        'INCIDENT_EVENT'::text,
        'KNOWLEDGE_BASE'::text
    ])
);

COMMIT;
