import React, { useState } from 'react';
import { Navbar } from '../components/Navbar';
import { LegalModal } from '../components/LegalModal';
import { CookieBanner } from '../components/CookieBanner';

export function MainLayout({ activeTab, onSelectTab, children }) {
  const [legalModalTab, setLegalModalTab] = useState(null);

  return (
    <div className="app-container">
      {/* Accessibility Skip-to-Content Link */}
      <a href="#main-content" className="skip-to-content">
        Skip to main content
      </a>

      {/* Top Navigation */}
      <Navbar activeTab={activeTab} onSelectTab={onSelectTab} />

      {/* Main Page Landmark */}
      <main id="main-content" role="main" className="main-content" tabIndex={-1}>
        {children}
      </main>

      {/* Footer Landmark */}
      <footer
        role="contentinfo"
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
          color: 'var(--text-muted)',
          fontSize: '12px',
          background: 'var(--bg-deep)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>OpsPilot</span>
          <span>•</span>
          <span>Enterprise IT Operations &amp; SRE Incident Response Copilot</span>
          <span>•</span>
          <span>&copy; {new Date().getFullYear()} All rights reserved.</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px' }}>
          <span>LangGraph Multi-Agent Architecture</span>
          <span aria-hidden="true">•</span>
          <span>PostgreSQL 15 Core</span>
          <span aria-hidden="true">•</span>
          <span>Pinecone Vector Engine (RAG)</span>
          <span aria-hidden="true">•</span>
          <span>OpenTelemetry &amp; Prometheus</span>
        </div>

        {/* Legal, Support, Contact Links */}
        <nav aria-label="Legal and contact links" style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <button
            onClick={() => setLegalModalTab('privacy')}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '11px' }}
            aria-label="Open Privacy Policy"
          >
            Privacy Policy
          </button>
          <span aria-hidden="true">•</span>
          <button
            onClick={() => setLegalModalTab('terms')}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '11px' }}
            aria-label="Open Terms of Service"
          >
            Terms of Service
          </button>
          <span aria-hidden="true">•</span>
          <button
            onClick={() => setLegalModalTab('refund')}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '11px' }}
            aria-label="Open Refund Policy"
          >
            Refund Policy
          </button>
          <span aria-hidden="true">•</span>
          <button
            onClick={() => setLegalModalTab('cookies')}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '11px' }}
            aria-label="Open Cookie Policy"
          >
            Cookie Policy
          </button>
          <span aria-hidden="true">•</span>
          <button
            onClick={() => setLegalModalTab('dpdp')}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '11px' }}
            aria-label="Open India DPDP Compliance details"
          >
            India DPDP
          </button>
          <span aria-hidden="true">•</span>
          <button
            onClick={() => setLegalModalTab('contact')}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '11px' }}
            aria-label="Open Business & Contact Details"
          >
            Contact
          </button>
          <span aria-hidden="true">•</span>
          <a
            href="mailto:support@opspilot.dev"
            style={{ color: 'var(--accent-cyan)', fontSize: '11px' }}
            aria-label="Send email to support"
          >
            support@opspilot.dev
          </a>
          <span aria-hidden="true">•</span>
          <a
            href="tel:+18005550199"
            style={{ color: 'var(--text-secondary)', fontSize: '11px' }}
            aria-label="Call support: plus 1 800 555 0199"
          >
            +1 (800) 555-0199
          </a>
        </nav>
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
