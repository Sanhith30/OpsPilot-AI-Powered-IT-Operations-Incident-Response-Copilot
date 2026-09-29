import React, { useState, useEffect, useRef } from 'react';
import { sendChatMessage, listChatSessions, getChatSession } from '../api/chat';
import { ChatSessionDrawer } from '../components/chat/ChatSessionDrawer';
import { ChatMessageItem } from '../components/chat/ChatMessageItem';
import { useToast } from '../context/ToastContext';

const STARTER_PROMPTS = [
  {
    icon: '🚨',
    title: 'Payment API Latency',
    prompt: 'What is causing high latency and errors on payment-api?',
  },
  {
    icon: '📋',
    title: 'Search Error Logs',
    prompt: 'Check recent error logs for payment-api and identify the failing queries.',
  },
  {
    icon: '📈',
    title: 'Database Pool Telemetry',
    prompt: 'Query active database connections and error rates for payment-api.',
  },
  {
    icon: '🧠',
    title: 'Predict Incident Risk',
    prompt: 'Run ML risk prediction on incident #1 and show contributing factors.',
  },
  {
    icon: '🚀',
    title: 'Recent Deployments',
    prompt: 'List recent deployments across all microservices and check if any coincided with errors.',
  },
];

export function ChatPage({ defaultIncidentId = null, onNavigateToIncident }) {
  const { addToast } = useToast();
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [incidentIdContext, setIncidentIdContext] = useState(defaultIncidentId);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending]);

  // Load user's chat sessions on mount
  const fetchSessions = async () => {
    try {
      setLoadingSessions(true);
      const data = await listChatSessions(50);
      setSessions(data || []);
      if (data && data.length > 0 && !activeSessionId) {
        // Select latest session by default if available
        loadSession(data[0].session_id);
      }
    } catch (err) {
      console.error('Failed to load chat sessions:', err);
    } finally {
      setLoadingSessions(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const loadSession = async (sessionId) => {
    try {
      setActiveSessionId(sessionId);
      const sess = await getChatSession(sessionId);
      if (sess && sess.messages) {
        setMessages(sess.messages);
        if (sess.incident_id) {
          setIncidentIdContext(sess.incident_id);
        }
      }
    } catch (err) {
      addToast(`Failed to load session ${sessionId}: ${err.message}`, 'error');
    }
  };

  const handleNewSession = () => {
    setActiveSessionId(null);
    setMessages([]);
    setInputMessage('');
    inputRef.current?.focus();
  };

  const handleSend = async (messageToSend) => {
    const text = (messageToSend || inputMessage).trim();
    if (!text || isSending) return;

    // Optimistically append user message to UI
    const tempUserMsg = {
      message_id: Date.now(),
      session_id: activeSessionId || 'temp',
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    setInputMessage('');
    setIsSending(true);

    try {
      const response = await sendChatMessage({
        message: text,
        session_id: activeSessionId || undefined,
        incident_id: incidentIdContext ? Number(incidentIdContext) : undefined,
      });

      // Update active session ID
      if (response.session_id) {
        setActiveSessionId(response.session_id);
      }

      // Append assistant message
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

      // Refresh sessions in drawer
      fetchSessions();
    } catch (err) {
      addToast(`Error communicating with copilot: ${err.message}`, 'error');
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        height: 'calc(100vh - 120px)',
        background: 'var(--bg-deep)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-subtle)',
        overflow: 'hidden',
        boxShadow: 'var(--shadow-md)',
      }}
    >
      {/* Left History Drawer */}
      <ChatSessionDrawer
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={loadSession}
        onNewSession={handleNewSession}
        loading={loadingSessions}
      />

      {/* Main Conversation Stream */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          background: 'var(--bg-main)',
        }}
      >
        {/* Chat Header Bar */}
        <div
          style={{
            padding: '16px 24px',
            borderBottom: '1px solid var(--border-subtle)',
            background: 'var(--bg-surface)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #00F2FE 0%, #0284C7 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#080C14',
                fontWeight: 800,
                fontSize: '16px',
                boxShadow: '0 0 12px rgba(0, 242, 254, 0.4)',
              }}
            >
              💬
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-highlight)', margin: 0 }}>
                  Ask OpsPilot Copilot
                </h2>
                <span
                  style={{
                    fontSize: '10px',
                    fontFamily: 'var(--font-mono)',
                    background: 'rgba(0, 242, 254, 0.12)',
                    color: 'var(--accent-cyan)',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    border: '1px solid rgba(0, 242, 254, 0.25)',
                  }}
                >
                  Autonomous LangGraph Multi-Tool
                </span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Ask in natural language — OpsPilot determines required tools, gathers grounded evidence, and synthesizes answers.
              </div>
            </div>
          </div>

          {/* Context badges & actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {incidentIdContext && (
              <span
                style={{
                  fontSize: '11px',
                  fontFamily: 'var(--font-mono)',
                  background: 'rgba(245, 158, 11, 0.1)',
                  color: 'var(--status-warning)',
                  padding: '3px 8px',
                  borderRadius: '4px',
                  border: '1px solid rgba(245, 158, 11, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <span>🚨 Bound to INC #{incidentIdContext}</span>
                <button
                  onClick={() => setIncidentIdContext(null)}
                  style={{ color: 'var(--text-muted)', fontSize: '10px' }}
                  title="Remove incident context"
                >
                  ✕
                </button>
              </span>
            )}
            <button
              onClick={handleNewSession}
              className="btn btn-secondary"
              style={{ fontSize: '11px', padding: '6px 12px' }}
            >
              + New Chat
            </button>
          </div>
        </div>

        {/* Message Stream Area */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {messages.length === 0 ? (
            <div
              style={{
                margin: 'auto',
                maxWidth: '680px',
                textAlign: 'center',
                padding: '40px 20px',
              }}
            >
              <div
                style={{
                  width: '56px',
                  height: '56px',
                  margin: '0 auto 16px',
                  borderRadius: '16px',
                  background: 'linear-gradient(135deg, rgba(0, 242, 254, 0.15) 0%, rgba(2, 132, 199, 0.25) 100%)',
                  border: '1px solid rgba(0, 242, 254, 0.4)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '28px',
                  boxShadow: '0 0 20px rgba(0, 242, 254, 0.25)',
                }}
              >
                🤖
              </div>
              <h3 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-highlight)', marginBottom: '8px' }}>
                Operational Investigation Copilot
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '24px' }}>
                OpsPilot executes a dynamic Reason &rarr; Tool &rarr; Synthesize loop with access to logs, metrics,
                database schema, deployments, RAG runbooks, and ML risk evaluation.
              </p>

              {/* Starter Prompts */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                  gap: '12px',
                  textAlign: 'left',
                }}
              >
                {STARTER_PROMPTS.map((sp, idx) => (
                  <div
                    key={idx}
                    onClick={() => handleSend(sp.prompt)}
                    style={{
                      padding: '12px 14px',
                      borderRadius: 'var(--radius-md)',
                      background: 'var(--bg-surface)',
                      border: '1px solid var(--border-subtle)',
                      cursor: 'pointer',
                      transition: 'all var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = 'var(--accent-cyan)';
                      e.currentTarget.style.transform = 'translateY(-2px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'var(--border-subtle)';
                      e.currentTarget.style.transform = 'translateY(0)';
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span>{sp.icon}</span>
                      <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-highlight)' }}>
                        {sp.title}
                      </span>
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                      {sp.prompt}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <ChatMessageItem key={msg.message_id} message={msg} />
              ))}

              {/* Thinking / Running indicator */}
              {isSending && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '14px 18px',
                    borderRadius: 'var(--radius-md)',
                    background: 'rgba(0, 242, 254, 0.05)',
                    border: '1px solid rgba(0, 242, 254, 0.2)',
                    marginBottom: '18px',
                    maxWidth: '460px',
                  }}
                >
                  <span className="spinner" style={{ width: '18px', height: '18px' }} />
                  <div>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                      OpsPilot is investigating...
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      Evaluating tools • Querying telemetry &amp; logs • Synthesizing answer
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Bar */}
        <div
          style={{
            padding: '16px 24px',
            borderTop: '1px solid var(--border-subtle)',
            background: 'var(--bg-surface)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-end',
              gap: '12px',
              background: '#080C14',
              border: '1px solid var(--border-medium)',
              borderRadius: 'var(--radius-lg)',
              padding: '8px 12px',
            }}
          >
            <textarea
              ref={inputRef}
              rows={1}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask OpsPilot anything (e.g. 'Why is error rate spiking on payment-api?')..."
              disabled={isSending}
              style={{
                flex: 1,
                background: 'transparent',
                border: 'none',
                outline: 'none',
                resize: 'none',
                color: 'var(--text-primary)',
                fontSize: '13px',
                lineHeight: 1.5,
                maxHeight: '120px',
              }}
            />

            <button
              onClick={() => handleSend()}
              disabled={!inputMessage.trim() || isSending}
              className="btn btn-primary"
              style={{
                padding: '8px 16px',
                borderRadius: 'var(--radius-md)',
                fontSize: '13px',
                fontWeight: 700,
                opacity: !inputMessage.trim() || isSending ? 0.4 : 1,
                cursor: !inputMessage.trim() || isSending ? 'not-allowed' : 'pointer',
              }}
            >
              {isSending ? (
                <span className="spinner" style={{ width: '14px', height: '14px' }} />
              ) : (
                <>
                  <span>Send</span>
                  <span>&rarr;</span>
                </>
              )}
            </button>
          </div>

          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: '8px',
              fontSize: '11px',
              color: 'var(--text-muted)',
            }}
          >
            <span>Press <strong>Enter</strong> to send, <strong>Shift+Enter</strong> for new line</span>
            <span style={{ color: 'var(--accent-cyan)' }}>Grounded Investigation • Zero Hallucination Policy</span>
          </div>
        </div>
      </div>
    </div>
  );
}
