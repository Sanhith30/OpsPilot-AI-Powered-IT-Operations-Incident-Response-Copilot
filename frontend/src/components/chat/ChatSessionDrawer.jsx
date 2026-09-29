import React from 'react';
import { formatRelativeTime } from '../../utils/formatters';

export function ChatSessionDrawer({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  loading,
}) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: 'var(--bg-surface)',
        borderRight: '1px solid var(--border-subtle)',
        width: '280px',
        minWidth: '280px',
      }}
    >
      {/* Top action: New Chat button */}
      <div style={{ padding: '16px', borderBottom: '1px solid var(--border-subtle)' }}>
        <button
          onClick={onNewSession}
          className="btn btn-primary"
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: '10px 14px',
            fontSize: '13px',
          }}
        >
          <span>✨</span>
          <span>New Investigation</span>
        </button>
      </div>

      {/* Sessions list */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '12px 8px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
        }}
      >
        <div
          style={{
            fontSize: '11px',
            fontWeight: 700,
            textTransform: 'uppercase',
            color: 'var(--text-muted)',
            letterSpacing: '0.05em',
            padding: '4px 8px',
          }}
        >
          Recent Sessions ({sessions.length})
        </div>

        {loading && sessions.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>
            <span className="spinner" style={{ width: '16px', height: '16px', display: 'inline-block', marginBottom: '8px' }} />
            <div>Loading sessions...</div>
          </div>
        ) : sessions.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>
            No prior sessions. Ask your first question!
          </div>
        ) : (
          sessions.map((sess) => {
            const isActive = sess.session_id === activeSessionId;
            return (
              <div
                key={sess.session_id}
                onClick={() => onSelectSession(sess.session_id)}
                style={{
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-md)',
                  background: isActive ? 'rgba(0, 242, 254, 0.08)' : 'transparent',
                  border: isActive ? '1px solid rgba(0, 242, 254, 0.3)' : '1px solid transparent',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span
                    style={{
                      fontSize: '13px',
                      fontWeight: isActive ? 700 : 500,
                      color: isActive ? 'var(--accent-cyan)' : 'var(--text-primary)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      maxWidth: '180px',
                    }}
                  >
                    {sess.title || 'Investigation Session'}
                  </span>
                  <span
                    style={{
                      fontSize: '10px',
                      fontFamily: 'var(--font-mono)',
                      background: 'rgba(255, 255, 255, 0.06)',
                      color: 'var(--text-muted)',
                      padding: '1px 5px',
                      borderRadius: '10px',
                    }}
                  >
                    {sess.message_count || 1}
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
                  <span>{formatRelativeTime(sess.updated_at || sess.created_at)}</span>
                  {sess.incident_id && (
                    <span style={{ color: 'var(--status-warning)' }}>
                      INC #{sess.incident_id}
                    </span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
