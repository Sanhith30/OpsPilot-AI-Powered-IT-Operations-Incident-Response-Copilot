-- Migration 022: Application Log Subsystem
-- Stores structured application log entries emitted by instrumented services.

CREATE TABLE IF NOT EXISTS core.app_logs (
    log_id          BIGSERIAL PRIMARY KEY,
    service_id      INTEGER       REFERENCES core.services(service_id) ON DELETE SET NULL,
    service_name    VARCHAR(120)  NOT NULL,
    level           VARCHAR(20)   NOT NULL CHECK (level IN ('DEBUG','INFO','WARNING','ERROR','CRITICAL')),
    message         TEXT          NOT NULL,
    logger_name     VARCHAR(255),
    trace_id        VARCHAR(64),
    span_id         VARCHAR(32),
    host            VARCHAR(255),
    environment     VARCHAR(50)   DEFAULT 'Production',
    extra           JSONB         DEFAULT '{}',
    logged_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_app_logs_service_id      ON core.app_logs(service_id);
CREATE INDEX IF NOT EXISTS idx_app_logs_level           ON core.app_logs(level);
CREATE INDEX IF NOT EXISTS idx_app_logs_logged_at       ON core.app_logs(logged_at DESC);
CREATE INDEX IF NOT EXISTS idx_app_logs_service_level   ON core.app_logs(service_id, level, logged_at DESC);
CREATE INDEX IF NOT EXISTS idx_app_logs_trace_id        ON core.app_logs(trace_id) WHERE trace_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_app_logs_message_gin     ON core.app_logs USING GIN (to_tsvector('english', message));

COMMENT ON TABLE  core.app_logs IS 'Structured application log entries from instrumented services.';
COMMENT ON COLUMN core.app_logs.level        IS 'Log severity level.';
COMMENT ON COLUMN core.app_logs.trace_id     IS 'Distributed trace correlation ID.';
COMMENT ON COLUMN core.app_logs.extra        IS 'Arbitrary structured metadata from the log record.';
