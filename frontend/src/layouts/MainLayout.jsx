import React, { useState } from 'react';
import { Navbar } from '../components/Navbar';
import { LegalModal } from '../components/LegalModal';
import { CookieBanner } from '../components/CookieBanner';

export function MainLayout({ activeTab, onSelectTab, children }) {
  const [legalModalTab, setLegalModalTab] = useState(null);
  const currentYear = new Date().getFullYear();

  return (
    <div className="app-container" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar activeTab={activeTab} onSelectTab={onSelectTab} />

      <main className="main-content" style={{ flex: 1 }}>
        {children}
      </main>

      <footer
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '16px 24px',
          backgroundColor: 'var(--bg-surface)',
          fontSize: '11px',
          color: 'var(--text-muted)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '14px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <span>© {currentYear} OpsPilot Autonomous SRE Platform</span>
          <span>•</span>
          <span>PostgreSQL 15 Core</span>
          <span>•</span>
          <span>Pinecone Vector Engine (RAG)</span>
          <span>•</span>
          <span>OpenTelemetry &amp; Prometheus</span>
        </div>

        {/* Working Footer Links for Legal, Support, and Phone */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          <button
            onClick={() => setLegalModalTab('privacy')}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '11px' }}
          >
            Privacy Policy
          </button>
          <span>•</span>
          <button
            onClick={() => setLegalModalTab('terms')}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '11px' }}
          >
            Terms of Service
          </button>
          <span>•</span>
          <button
            onClick={() => setLegalModalTab('cookies')}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '11px' }}
          >
            Cookie Policy
          </button>
          <span>•</span>
          <a
            href="mailto:support@opspilot.local"
            style={{ color: 'var(--accent-cyan)', fontSize: '11px' }}
          >
            support@opspilot.local
          </a>
          <span>•</span>
          <a
            href="tel:+918001234567"
            style={{ color: 'var(--text-secondary)', fontSize: '11px' }}
          >
            +91 800 123 4567
          </a>
        </div>
      </footer>

      {/* Cookie Consent Banner */}
      <CookieBanner onOpenCookiePolicy={() => setLegalModalTab('cookies')} />

      {/* Legal & Privacy Modal */}
      {legalModalTab && (
        <LegalModal
          initialTab={legalModalTab}
          onClose={() => setLegalModalTab(null)}
        />
      )}
    </div>
  );
}
