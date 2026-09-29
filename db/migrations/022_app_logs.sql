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

DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'opspilot_app') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON core.app_logs TO opspilot_app;
        GRANT USAGE, SELECT ON SEQUENCE core.app_logs_log_id_seq TO opspilot_app;
    END IF;
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'opspilot_owner') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON core.app_logs TO opspilot_owner;
    END IF;
END $$;

-- Seed initial representative error logs for payment-api
INSERT INTO core.app_logs (service_id, service_name, level, message, logger_name, trace_id, host, environment, extra, logged_at)
VALUES
(1, 'payment-api', 'ERROR', 'Database connection timeout: pool exhausted after 30000ms waiting for active connection slot', 'payment.db.pool', 'c607cdcc14a24890', 'ip-10-0-2-14', 'Production', '{"error_code": "DB_POOL_EXHAUSTED", "connections_active": 100, "connections_max": 100}'::jsonb, NOW() - INTERVAL '15 minutes'),
(1, 'payment-api', 'ERROR', 'HTTP 504 Gateway Timeout: failed to process payment checkout request due to upstream DB pool starvation', 'payment.api.handler', 'c607cdcc14a24890', 'ip-10-0-2-14', 'Production', '{"endpoint": "/v1/payments/checkout", "http_status": 504}'::jsonb, NOW() - INTERVAL '14 minutes'),
(1, 'payment-api', 'WARNING', 'High database connection wait time: current wait queue length 47 requests', 'payment.db.pool', 'f501fec4890b2123', 'ip-10-0-2-14', 'Production', '{"wait_queue_length": 47}'::jsonb, NOW() - INTERVAL '20 minutes'),
(1, 'payment-api', 'ERROR', 'Database connection pool saturation: active connections at 94% threshold', 'payment.telemetry', '92556b931984210a', 'ip-10-0-2-14', 'Production', '{"metric": "db_connection_pool", "value": 0.94}'::jsonb, NOW() - INTERVAL '10 minutes')
ON CONFLICT DO NOTHING;
