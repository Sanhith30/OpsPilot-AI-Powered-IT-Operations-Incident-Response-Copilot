import React from 'react';

export function NotFoundPage({ onNavigateHome }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        textAlign: 'center',
        padding: '40px 20px',
      }}
    >
      <div
        style={{
          width: '72px',
          height: '72px',
          borderRadius: '50%',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '32px',
          marginBottom: '20px',
        }}
      >
        🔍
      </div>
      <h1 style={{ fontSize: '28px', fontWeight: 800, color: 'var(--text-highlight)', marginBottom: '8px' }}>
        404 — Resource Not Found
      </h1>
      <p style={{ fontSize: '14px', color: 'var(--text-secondary)', maxWidth: '460px', marginBottom: '24px' }}>
        The incident, runbook, or operational view you requested does not exist or has been archived. Return to the primary operations command center.
      </p>
      <button className="btn btn-primary" onClick={onNavigateHome}>
        ← Back to Operations Dashboard
      </button>
    </div>
  );
}
