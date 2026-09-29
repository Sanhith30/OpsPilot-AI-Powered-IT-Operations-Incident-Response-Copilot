import React from 'react';
import { PersonaSwitcher } from './PersonaSwitcher';

export function Navbar({ activeTab, onSelectTab }) {
  const navItems = [
    { id: 'chat', label: 'Ask Copilot', icon: '💬', badge: 'AI' },
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'incidents', label: 'Incidents & Triage', icon: '🚨' },
    { id: 'remediations', label: 'Remediations', icon: '⚡' },
    { id: 'knowledge', label: 'Knowledge (RAG)', icon: '📚' },
    { id: 'audit', label: 'Audit & Telemetry', icon: '🛡️' },
  ];

  return (
    <header
      style={{
        background: 'var(--bg-glass)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        borderBottom: '1px solid var(--border-subtle)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}
    >
      <div
        style={{
          maxWidth: '1440px',
          margin: '0 auto',
          padding: '0 24px',
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
          <div
            onClick={() => onSelectTab('dashboard')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              cursor: 'pointer',
            }}
          >
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: 'var(--radius-md)',
                background: 'linear-gradient(135deg, #00F2FE 0%, #0284C7 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 16px rgba(0, 242, 254, 0.4)',
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#080C14" strokeWidth="2.5">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
                <path d="M2 12h20" />
              </svg>
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '18px', fontWeight: 800, letterSpacing: '-0.02em', color: '#FFFFFF' }}>
                  OpsPilot
                </span>
                <span
                  style={{
                    fontSize: '10px',
                    fontFamily: 'var(--font-mono)',
                    background: 'rgba(0, 242, 254, 0.1)',
                    color: 'var(--accent-cyan)',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    border: '1px solid rgba(0, 242, 254, 0.25)',
                  }}
                >
                  v0.20
                </span>
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Autonomous SRE Copilot
              </div>
            </div>
          </div>

          {/* Navigation links */}
          <nav style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectTab(item.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 14px',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '13px',
                    fontWeight: 600,
                    color: isActive ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                    background: isActive ? 'rgba(0, 242, 254, 0.08)' : 'transparent',
                    border: isActive ? '1px solid rgba(0, 242, 254, 0.25)' : '1px solid transparent',
                    transition: 'all var(--transition-fast)',
                  }}
                >
                  <span>{item.icon}</span>
                  <span>{item.label}</span>
                  {item.badge && (
                    <span
                      style={{
                        fontSize: '9px',
                        fontWeight: 800,
                        padding: '1px 5px',
                        borderRadius: '4px',
                        background: 'linear-gradient(135deg, #00F2FE 0%, #0284C7 100%)',
                        color: '#080C14',
                        boxShadow: '0 0 8px rgba(0, 242, 254, 0.4)',
                      }}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Right side: Live engine status & Persona Switcher */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: 'var(--radius-full)',
              background: 'rgba(16, 185, 129, 0.08)',
              border: '1px solid rgba(16, 185, 129, 0.2)',
              fontSize: '11px',
              color: 'var(--status-healthy)',
            }}
          >
            <span
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                background: 'var(--status-healthy)',
                boxShadow: '0 0 8px var(--status-healthy)',
              }}
            />
            <span style={{ fontWeight: 600 }}>FastAPI Connected</span>
          </div>

          <PersonaSwitcher />
        </div>
      </div>
    </header>
  );
}
