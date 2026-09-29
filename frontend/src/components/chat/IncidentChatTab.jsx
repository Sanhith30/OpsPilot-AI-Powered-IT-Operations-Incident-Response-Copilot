import React, { useState, useEffect, useRef } from 'react';
import { sendChatMessage, listChatSessions, getChatSession } from '../../api/chat';
import { ChatMessageItem } from './ChatMessageItem';
import { useToast } from '../../context/ToastContext';

export function IncidentChatTab({ incident }) {
  const { addToast } = useToast();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [isSending, setIsSending] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending]);

  // Look for any existing session bound to this incident
  useEffect(() => {
    const findIncidentSession = async () => {
      try {
        setLoadingHistory(true);
        const sessions = await listChatSessions(50);
        const match = sessions.find((s) => s.incident_id === incident.incident_id);
        if (match) {
          setSessionId(match.session_id);
          const detail = await getChatSession(match.session_id);
          if (detail && detail.messages) {
            setMessages(detail.messages);
          }
        }
      } catch (err) {
        console.error('Could not fetch prior incident chat session:', err);
      } finally {
        setLoadingHistory(false);
      }
    };

    if (incident?.incident_id) {
      findIncidentSession();
    }
  }, [incident?.incident_id]);

  const handleSend = async (customPrompt) => {
    const text = (customPrompt || inputMessage).trim();
    if (!text || isSending) return;

    const tempMsg = {
      message_id: Date.now(),
      session_id: sessionId || 'temp',
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, tempMsg]);
    setInputMessage('');
    setIsSending(true);

    try {
      const response = await sendChatMessage({
        message: text,
        session_id: sessionId || undefined,
        incident_id: incident.incident_id,
      });

      if (response.session_id) {
        setSessionId(response.session_id);
      }

      const assistantMsg = {
        message_id: Date.now() + 1,
        session_id: response.session_id,
        role: 'assistant',
        content: response.answer,
        tool_trace: response.tool_trace || [],
        citations: response.citations || [],
        risk: response.risk || null,
        investigation_id: response.investigation_id || null,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      addToast(`Error in copilot investigation: ${err.message}`, 'error');
    } finally {
      setIsSending(false);
    }
  };

  const incidentSuggestions = [
    `Search error logs for incident #${incident.incident_id}`,
    `Query connection pool metrics and latency for this service`,
    `What runbook remediation applies to this incident?`,
    `Predict failure risk for incident #${incident.incident_id}`,
  ];

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '620px',
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        overflow: 'hidden',
      }}
    >
      {/* Tab Header info */}
      <div
        style={{
          padding: '12px 20px',
          background: 'var(--bg-surface)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center' }} aria-hidden="true">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
          </span>
          <span style={{ fontWeight: 700, color: 'var(--text-highlight)', fontSize: '14px' }}>
            Interactive Copilot Investigation - Incident #{incident.incident_id}
          </span>
          <span
            style={{
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              background: 'rgba(0, 242, 254, 0.1)',
              color: 'var(--accent-cyan)',
              padding: '2px 6px',
              borderRadius: '4px',
            }}
          >
            Context Bound
          </span>
        </div>

        {sessionId && (
          <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
            Session: {sessionId}
          </span>
        )}
      </div>

      {/* Message stream */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {loadingHistory ? (
          <div style={{ margin: 'auto', textAlign: 'center', color: 'var(--text-muted)' }}>
            <span className="spinner" style={{ width: '20px', height: '20px', marginBottom: '8px' }} />
            <div>Loading investigation history...</div>
          </div>
        ) : messages.length === 0 ? (
          <div style={{ margin: 'auto', maxWidth: '520px', textAlign: 'center', padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'center', color: 'var(--accent-cyan)', marginBottom: '8px' }} aria-hidden="true">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
            </div>
            <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-highlight)', marginBottom: '6px' }}>
              Investigate Incident #{incident.incident_id} in Natural Language
            </h4>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: 1.5 }}>
              Ask OpsPilot to inspect logs, correlate metrics, evaluate runbooks, or assess blast radius for this incident.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', textAlign: 'left' }}>
              {incidentSuggestions.map((sug, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(sug)}
                  style={{
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-main)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--accent-cyan)',
                    fontSize: '12px',
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'border-color 0.15s',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-cyan)')}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-subtle)')}
                >
                  <span style={{ marginRight: '6px' }}>&rsaquo;</span> {sug}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((m) => (
              <ChatMessageItem key={m.message_id} message={m} />
            ))}

            {isSending && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '12px 16px',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(0, 242, 254, 0.05)',
                  border: '1px solid rgba(0, 242, 254, 0.2)',
                  maxWidth: '360px',
                  marginBottom: '16px',
                }}
              >
                <span className="spinner" style={{ width: '16px', height: '16px' }} />
                <span style={{ fontSize: '12px', color: 'var(--accent-cyan)', fontWeight: 600 }}>
                  OpsPilot is investigating...
                </span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input bar */}
      <div
        style={{
          padding: '12px 20px',
          background: 'var(--bg-surface)',
          borderTop: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={`Ask OpsPilot about incident #${incident.incident_id}...`}
            disabled={isSending}
            style={{
              flex: 1,
              background: '#0B0F17',
              border: '1px solid var(--border-medium)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 14px',
              fontSize: '13px',
              color: 'var(--text-primary)',
              outline: 'none',
            }}
          />
          <button
            onClick={() => handleSend()}
            disabled={!inputMessage.trim() || isSending}
            className="btn btn-primary"
            style={{ padding: '0 18px', fontSize: '13px' }}
          >
            {isSending ? <span className="spinner" /> : 'Ask Copilot'}
          </button>
        </div>
      </div>
    </div>
  );
}
