import React, { useState, useEffect } from 'react';

export function CookieBanner({ onOpenCookiePolicy }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem('opspilot_cookie_consent');
    if (!consent) {
      setVisible(true);
    }
  }, []);

  const handleConsent = (choice) => {
    localStorage.setItem('opspilot_cookie_consent', choice);
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '20px',
        left: '20px',
        right: '20px',
        maxWidth: '820px',
        margin: '0 auto',
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-medium)',
        borderRadius: 'var(--radius-lg)',
        padding: '16px 20px',
        boxShadow: 'var(--shadow-lg)',
        zIndex: 900,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px',
      }}
    >
      <div style={{ flex: '1 1 450px' }}>
        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-highlight)', marginBottom: '4px' }}>
          🛡️ Privacy &amp; Essential Storage Notice
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
          OpsPilot uses strictly essential local tokens for secure JWT authentication and role-based incident operations. We do not use advertising or tracking cookies. Compliant with DPDP Act 2023.
        </p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
        <button
          onClick={onOpenCookiePolicy}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--accent-cyan)',
            fontSize: '12px',
            cursor: 'pointer',
            textDecoration: 'underline',
            padding: '6px 8px',
          }}
        >
          Cookie Policy
        </button>
        <button
          onClick={() => handleConsent('essential')}
          className="btn btn-secondary"
          style={{ padding: '6px 14px', fontSize: '12px' }}
        >
          Essential Only
        </button>
        <button
          onClick={() => handleConsent('accepted')}
          className="btn btn-primary"
          style={{ padding: '6px 16px', fontSize: '12px' }}
        >
          Accept All
        </button>
      </div>
    </div>
  );
}
