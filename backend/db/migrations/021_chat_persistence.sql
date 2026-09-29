BEGIN;

CREATE TABLE IF NOT EXISTS core.chat_sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES core.users(user_id) ON DELETE CASCADE,
    incident_id BIGINT REFERENCES core.incidents(incident_id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL DEFAULT 'New Conversation',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS core.chat_messages (
    message_id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL REFERENCES core.chat_sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    tool_trace JSONB NOT NULL DEFAULT '[]'::jsonb,
    citations JSONB NOT NULL DEFAULT '[]'::jsonb,
    risk JSONB NULL,
    investigation_id BIGINT REFERENCES core.investigations(investigation_id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user
    ON core.chat_sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_incident
    ON core.chat_sessions(incident_id);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at
    ON core.chat_sessions(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session
    ON core.chat_messages(session_id);

CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at
    ON core.chat_messages(created_at ASC);

GRANT SELECT, INSERT, UPDATE, DELETE ON core.chat_sessions TO opspilot_app;
GRANT SELECT ON core.chat_sessions TO opspilot_agent_ro;

GRANT SELECT, INSERT, UPDATE, DELETE ON core.chat_messages TO opspilot_app;
GRANT SELECT ON core.chat_messages TO opspilot_agent_ro;

GRANT USAGE, SELECT ON SEQUENCE core.chat_messages_message_id_seq TO opspilot_app;

COMMIT;
