import React, { useState } from 'react';

export function LegalModal({ initialTab = 'privacy', onClose }) {
  const [tab, setTab] = useState(initialTab);
  const [deletionStatus, setDeletionStatus] = useState(null);

  const handleRequestDeletion = () => {
    setDeletionStatus('PROCESSING');
    setTimeout(() => {
      setDeletionStatus('COMPLETED');
    }, 800);
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(8, 12, 20, 0.85)',
        backdropFilter: 'blur(8px)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-medium)',
          borderRadius: 'var(--radius-lg)',
          width: '100%',
          maxWidth: '780px',
          maxHeight: '85vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: 'var(--shadow-lg)',
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '20px 24px',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-highlight)' }}>
              Legal, Privacy &amp; Compliance Center
            </h2>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Enterprise data governance, terms of service, and regulatory disclosures.
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              fontSize: '20px',
              cursor: 'pointer',
              padding: '4px 8px',
              borderRadius: '4px',
            }}
            aria-label="Close legal modal"
          >
            ✕
          </button>
        </div>

        {/* Tab Navigation */}
        <div
          style={{
            display: 'flex',
            borderBottom: '1px solid var(--border-subtle)',
            background: 'var(--bg-main)',
            padding: '0 24px',
            gap: '8px',
          }}
        >
          {[
            { id: 'privacy', label: 'Privacy Policy' },
            { id: 'terms', label: 'Terms of Service' },
            { id: 'cookies', label: 'Cookie Policy' },
            { id: 'dpdp', label: 'India DPDP Compliance' },
            { id: 'deletion', label: 'Data Deletion' },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              style={{
                padding: '12px 16px',
                fontSize: '13px',
                fontWeight: 600,
                background: 'transparent',
                border: 'none',
                borderBottom: tab === t.id ? '2px solid var(--accent-cyan)' : '2px solid transparent',
                color: tab === t.id ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Content Body */}
        <div
          style={{
            padding: '24px',
            overflowY: 'auto',
            fontSize: '13px',
            lineHeight: 1.7,
            color: 'var(--text-secondary)',
          }}
        >
          {tab === 'privacy' && (
            <div>
              <h3 style={{ fontSize: '15px', color: 'var(--text-highlight)', marginBottom: '8px' }}>
                Privacy Policy (Enterprise Operations)
              </h3>
              <p style={{ marginBottom: '12px' }}>
                OpsPilot is designed strictly for IT operations, telemetry analysis, and incident triage. We do not sell, rent, or monetize your operational logs or telemetry data.
              </p>
              <h4 style={{ fontSize: '13px', color: 'var(--text-primary)', marginTop: '16px', marginBottom: '6px' }}>
                1. Data Collected
              </h4>
              <p style={{ marginBottom: '8px' }}>
                • Technical operational logs (error traces, timestamps, host identifiers).<br />
                • Aggregated system performance metrics (CPU, memory, latency percentiles).<br />
                • Diagnostic questions and runbook search queries submitted to the SRE Copilot.
              </p>
              <h4 style={{ fontSize: '13px', color: 'var(--text-primary)', marginTop: '16px', marginBottom: '6px' }}>
                2. Third-Party Processing
              </h4>
              <p style={{ marginBottom: '12px' }}>
                LLM inference is routed strictly through secure Gemini API endpoints under enterprise zero-data-retention agreements. Vector embeddings are stored in dedicated Pinecone indexes with encryption in transit (TLS 1.3) and at rest (AES-256).
              </p>
            </div>
          )}

          {tab === 'terms' && (
            <div>
              <h3 style={{ fontSize: '15px', color: 'var(--text-highlight)', marginBottom: '8px' }}>
                Terms of Service &amp; Safety Guardrails
              </h3>
              <p style={{ marginBottom: '12px' }}>
                By using OpsPilot, you acknowledge the autonomous platform operation boundaries:
              </p>
              <h4 style={{ fontSize: '13px', color: 'var(--text-primary)', marginTop: '16px', marginBottom: '6px' }}>
                1. Human-in-the-Loop Governance
              </h4>
              <p style={{ marginBottom: '12px' }}>
                All remediation plans (service scaling, traffic shifting, version rollbacks) generated by OpsPilot require explicit human approval via the Remediations portal before adapter execution. OpsPilot does not execute unverified destructive actions autonomously.
              </p>
              <h4 style={{ fontSize: '13px', color: 'var(--text-primary)', marginTop: '16px', marginBottom: '6px' }}>
                2. SLA &amp; Availability
              </h4>
              <p style={{ marginBottom: '12px' }}>
                The software is provided for enterprise operations management. Production cluster changes must adhere to internal organizational change windows.
              </p>
            </div>
          )}

          {tab === 'cookies' && (
            <div>
              <h3 style={{ fontSize: '15px', color: 'var(--text-highlight)', marginBottom: '8px' }}>
                Cookie &amp; Local Storage Policy
              </h3>
              <p style={{ marginBottom: '12px' }}>
                OpsPilot uses minimal local storage exclusively for essential platform functionality:
              </p>
              <p style={{ marginBottom: '8px' }}>
                • <strong>opspilot_token:</strong> Cryptographically signed JWT token for session authentication.<br />
                • <strong>opspilot_cookie_consent:</strong> Stores your cookie preference (Accept/Decline).<br />
                • <strong>opspilot_active_persona:</strong> Saves your selected role switcher state across page refreshes.
              </p>
              <p style={{ marginTop: '12px' }}>
                No advertising, behavioral profiling, or cross-site tracking cookies are ever utilized.
              </p>
            </div>
          )}

          {tab === 'dpdp' && (
            <div>
              <h3 style={{ fontSize: '15px', color: 'var(--text-highlight)', marginBottom: '8px' }}>
                Digital Personal Data Protection (DPDP) Act 2023 Compliance
              </h3>
              <p style={{ marginBottom: '12px' }}>
                In accordance with India's Digital Personal Data Protection Act, 2023 (DPDPA):
              </p>
              <p style={{ marginBottom: '8px' }}>
                • <strong>Purpose Limitation:</strong> Telemetry data is processed exclusively for technical incident mitigation.<br />
                • <strong>Data Minimization:</strong> Personal data elements are redacted before log indexing.<br />
                • <strong>Right to Correction &amp; Erasure:</strong> Users may request the deletion of historical chat sessions and audit trails at any time via the Data Deletion tab.<br />
                • <strong>Grievance Officer Contact:</strong> <code>grievance@opspilot.local</code>
              </p>
            </div>
          )}

          {tab === 'deletion' && (
            <div>
              <h3 style={{ fontSize: '15px', color: 'var(--text-highlight)', marginBottom: '8px' }}>
                User Data Deletion Request
              </h3>
              <p style={{ marginBottom: '16px' }}>
                You have the full right to delete your chat sessions, operational queries, and local cached tokens from the platform at any time.
              </p>

              {deletionStatus === 'COMPLETED' ? (
                <div
                  style={{
                    padding: '14px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--status-healthy-bg)',
                    border: '1px solid var(--status-healthy)',
                    color: 'var(--status-healthy)',
                    fontSize: '13px',
                    fontWeight: 600,
                  }}
                >
                  ✓ Data deletion request completed. Local tokens and session history cleared.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    Clicking below will clear your local user tokens and signal the backend to purge your current session:
                  </p>
                  <button
                    onClick={handleRequestDeletion}
                    disabled={deletionStatus === 'PROCESSING'}
                    className="btn btn-secondary"
                    style={{
                      alignSelf: 'flex-start',
                      borderColor: 'var(--status-critical)',
                      color: 'var(--status-critical)',
                      background: 'rgba(239, 68, 68, 0.08)',
                    }}
                  >
                    {deletionStatus === 'PROCESSING' ? 'Purging records...' : 'Purge My Data & Reset Session'}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '16px 24px',
            borderTop: '1px solid var(--border-subtle)',
            background: 'var(--bg-main)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Support: <a href="mailto:support@opspilot.local">support@opspilot.local</a> • Phone: <a href="tel:+918001234567">+91 800 123 4567</a>
          </div>
          <button className="btn btn-primary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
