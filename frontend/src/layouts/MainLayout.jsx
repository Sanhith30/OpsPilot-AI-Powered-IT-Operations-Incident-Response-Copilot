import React from 'react';
import { Navbar } from '../components/Navbar';

export function MainLayout({ activeTab, onSelectTab, children }) {
  return (
    <div className="app-container">
      <Navbar activeTab={activeTab} onSelectTab={onSelectTab} />

      <main className="main-content">
        {children}
      </main>

      <footer
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '16px 24px',
          background: 'var(--bg-main)',
          fontSize: '11px',
          color: 'var(--text-muted)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span>© 2026 OpsPilot Autonomous SRE Platform</span>
          <span>•</span>
          <span>PostgreSQL 16 Engine</span>
          <span>•</span>
          <span>Pinecone Vector Store (Threshold: 0.65)</span>
          <span>•</span>
          <span>OpenTelemetry &amp; Prometheus Telemetry</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ color: 'var(--status-healthy)' }}>● AI Recommends. Human Approves. Registered Adapters Execute.</span>
        </div>
      </footer>
    </div>
  );
}
