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
          color: 'var(--status-critical)',
          marginBottom: '20px',
        }}
        aria-hidden="true"
      >
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
      </div>
      <h1 style={{ fontSize: '28px', fontWeight: 800, color: 'var(--text-highlight)', marginBottom: '8px' }}>
        404: Resource Not Found
      </h1>
      <p style={{ fontSize: '14px', color: 'var(--text-secondary)', maxWidth: '460px', marginBottom: '24px' }}>
        The incident, runbook, or operational view you requested does not exist or has been archived. Return to the primary operations command center.
      </p>
      <button className="btn btn-primary" onClick={onNavigateHome}>
        Back to Operations Dashboard
      </button>
    </div>
  );
}
