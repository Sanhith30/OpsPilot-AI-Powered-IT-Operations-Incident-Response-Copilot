-- Migration 023: Service Metrics Subsystem
-- Stores time-series operational metrics (CPU, memory, latency, error rate, etc.)
-- for each instrumented service instance.

CREATE TABLE IF NOT EXISTS core.service_metrics (
    metric_id       BIGSERIAL PRIMARY KEY,
    service_id      INTEGER       NOT NULL REFERENCES core.services(service_id) ON DELETE CASCADE,
    service_name    VARCHAR(120)  NOT NULL,
    instance_id     VARCHAR(255),
    environment     VARCHAR(50)   DEFAULT 'Production',
    metric_name     VARCHAR(120)  NOT NULL,
    metric_value    DOUBLE PRECISION NOT NULL,
    unit            VARCHAR(40),
    dimensions      JSONB         DEFAULT '{}',
    recorded_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_svc_metrics_service_id    ON core.service_metrics(service_id);
CREATE INDEX IF NOT EXISTS idx_svc_metrics_name_time     ON core.service_metrics(service_id, metric_name, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_svc_metrics_recorded_at   ON core.service_metrics(recorded_at DESC);

DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'opspilot_app') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON core.service_metrics TO opspilot_app;
        GRANT USAGE, SELECT ON SEQUENCE core.service_metrics_metric_id_seq TO opspilot_app;
    END IF;
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'opspilot_owner') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON core.service_metrics TO opspilot_owner;
    END IF;
END $$;

-- Seed representative metrics for payment-api, auth-service, and api-gateway
INSERT INTO core.service_metrics (service_id, service_name, metric_name, metric_value, unit, environment, recorded_at)
SELECT
    s.service_id, s.service_name,
    m.metric_name, m.metric_value, m.unit, 'Production',
    NOW() - (m.offset_mins || ' minutes')::INTERVAL
FROM core.services s
CROSS JOIN (VALUES
    ('cpu_usage_percent',   72.4,  'percent',      '5'),
    ('cpu_usage_percent',   68.1,  'percent',      '10'),
    ('cpu_usage_percent',   91.2,  'percent',      '15'),
    ('memory_usage_mb',     3841,  'megabytes',    '5'),
    ('memory_usage_mb',     3720,  'megabytes',    '10'),
    ('error_rate',          0.034, 'ratio',        '5'),
    ('error_rate',          0.021, 'ratio',        '10'),
    ('error_rate',          0.156, 'ratio',        '15'),
    ('p99_latency_ms',      820,   'milliseconds', '5'),
    ('p99_latency_ms',      640,   'milliseconds', '10'),
    ('request_rate_rps',    1240,  'rps',          '5'),
    ('request_rate_rps',    1185,  'rps',          '10'),
    ('db_connection_pool',  94.0,  'percent',      '5'),
    ('db_connection_pool',  88.0,  'percent',      '10')
) AS m(metric_name, metric_value, unit, offset_mins)
WHERE s.service_name IN ('payment-api', 'auth-service', 'api-gateway')
ON CONFLICT DO NOTHING;
