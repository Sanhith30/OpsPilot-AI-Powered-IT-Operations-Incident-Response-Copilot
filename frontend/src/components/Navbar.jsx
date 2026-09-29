import React, { useState } from 'react';
import { PersonaSwitcher } from './PersonaSwitcher';

export function Navbar({ activeTab, onSelectTab }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { id: 'chat',         label: 'Ask Copilot',       icon: NavIconChat },
    { id: 'dashboard',   label: 'Dashboard',          icon: NavIconDashboard },
    { id: 'incidents',   label: 'Incidents & Triage', icon: NavIconIncidents },
    { id: 'remediations',label: 'Remediations',       icon: NavIconRemediation },
    { id: 'knowledge',   label: 'Knowledge (RAG)',    icon: NavIconKnowledge },
    { id: 'audit',       label: 'Audit & Telemetry',  icon: NavIconAudit },
  ];

  const handleNavClick = (id) => {
    onSelectTab(id);
    setMobileMenuOpen(false);
  };

  return (
    <header
      role="banner"
      style={{
        backgroundColor: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border-subtle)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      <div
        style={{
          maxWidth: '1440px',
          margin: '0 auto',
          padding: '0 20px',
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
        }}
      >
        {/* Brand Logo - clickable to dashboard */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div
            onClick={() => onSelectTab('dashboard')}
            role="button"
            tabIndex={0}
            aria-label="OpsPilot Home - go to Operations Dashboard"
            onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSelectTab('dashboard')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              cursor: 'pointer',
              userSelect: 'none',
            }}
          >
            <div
              style={{
                width: '34px',
                height: '34px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--accent-cyan)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#080C14',
                flexShrink: 0,
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
                <path d="M2 12h20" />
              </svg>
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '17px', fontWeight: 800, color: 'var(--text-highlight)' }}>
                  OpsPilot
                </span>
                <span
                  style={{
                    fontSize: '10px',
                    fontFamily: 'var(--font-mono)',
                    backgroundColor: 'rgba(0, 242, 254, 0.1)',
                    color: 'var(--accent-cyan)',
                    padding: '1px 5px',
                    borderRadius: '4px',
                    border: '1px solid rgba(0, 242, 254, 0.25)',
                    fontWeight: 600,
                  }}
                >
                  v0.20
                </span>
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Autonomous SRE Copilot
              </div>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="desktop-nav" aria-label="Main navigation" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => handleNavClick(item.id)}
                  aria-current={isActive ? 'page' : undefined}
                  aria-label={item.label}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '13px',
                    fontWeight: 600,
                    color: isActive ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                    backgroundColor: isActive ? 'rgba(0, 242, 254, 0.08)' : 'transparent',
                    border: isActive ? '1px solid rgba(0, 242, 254, 0.25)' : '1px solid transparent',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <Icon size={14} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Right Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            className="engine-status"
            aria-label="API connection status: connected"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: 'var(--radius-full)',
              backgroundColor: 'rgba(16, 185, 129, 0.08)',
              border: '1px solid rgba(16, 185, 129, 0.2)',
              fontSize: '11px',
              color: 'var(--status-healthy)',
            }}
          >
            <span
              aria-hidden="true"
              style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--status-healthy)', flexShrink: 0 }}
            />
            <span style={{ fontWeight: 600 }}>FastAPI Connected</span>
          </div>

          <PersonaSwitcher />

          {/* Mobile Hamburger Button */}
          <button
            className="mobile-menu-btn"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-nav-drawer"
            style={{
              background: 'transparent',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--text-primary)',
              padding: '8px 10px',
              cursor: 'pointer',
              display: 'none',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              {mobileMenuOpen ? (
                <path d="M18 6L6 18M6 6l12 12" />
              ) : (
                <path d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Drawer Navigation */}
      {mobileMenuOpen && (
        <div
          id="mobile-nav-drawer"
          role="navigation"
          aria-label="Mobile navigation"
          style={{
            backgroundColor: 'var(--bg-surface)',
            borderTop: '1px solid var(--border-subtle)',
            padding: '12px 20px 16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}
        >
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                aria-current={isActive ? 'page' : undefined}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '14px',
                  fontWeight: 600,
                  textAlign: 'left',
                  color: isActive ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                  backgroundColor: isActive ? 'rgba(0, 242, 254, 0.08)' : 'transparent',
                  border: isActive ? '1px solid rgba(0, 242, 254, 0.25)' : '1px solid transparent',
                  cursor: 'pointer',
                }}
              >
                <Icon size={16} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </header>
  );
}

/* ── Inline SVG icon components (no external library dependency) ── */
function NavIconChat({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}
function NavIconDashboard({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
      <rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" />
    </svg>
  );
}
function NavIconIncidents({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  );
}
function NavIconRemediation({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  );
}
function NavIconKnowledge({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
    </svg>
  );
}
function NavIconAudit({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  );
}
