import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { DEMO_PERSONAS } from '../types/constants';

export function PersonaSwitcher() {
  const { currentUser, activePersona, switchPersona, loading } = useAuth();
  const { addToast } = useToast();
  const [isOpen, setIsOpen] = useState(false);

  const handleSelect = async (persona) => {
    try {
      await switchPersona(persona);
      setIsOpen(false);
      addToast(`Switched persona to ${persona.name} (${persona.role})`, 'success');
    } catch (err) {
      addToast(`Failed to authenticate as ${persona.name}: ${err.message}`, 'error');
    }
  };

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '6px 12px',
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-medium)',
          borderRadius: 'var(--radius-full)',
          transition: 'all var(--transition-fast)',
        }}
        title="Switch RBAC Persona to test authorization barriers"
      >
        <span
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: 'var(--accent-cyan)',
            boxShadow: '0 0 8px var(--accent-cyan)',
          }}
        />
        <div style={{ display: 'flex', flexDirection: 'column', textAlign: 'left' }}>
          <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-highlight)' }}>
            {activePersona?.name || 'Authenticating...'}
          </span>
          <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
            {activePersona?.roleName}
          </span>
        </div>
        <span
          style={{
            fontSize: '11px',
            background: 'rgba(0, 242, 254, 0.15)',
            color: 'var(--accent-cyan)',
            padding: '2px 6px',
            borderRadius: '4px',
            fontWeight: 700,
          }}
        >
          {activePersona?.badge}
        </span>
        <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>▼</span>
      </button>

      {isOpen && (
        <>
          <div
            style={{ position: 'fixed', inset: 0, zIndex: 99 }}
            onClick={() => setIsOpen(false)}
          />
          <div
            style={{
              position: 'absolute',
              top: '110%',
              right: 0,
              zIndex: 100,
              width: '320px',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-medium)',
              borderRadius: 'var(--radius-lg)',
              boxShadow: 'var(--shadow-lg)',
              padding: '8px',
              animation: 'modalIn 150ms ease-out',
            }}
          >
            <div style={{ padding: '8px 10px', borderBottom: '1px solid var(--border-subtle)', marginBottom: '6px' }}>
              <div style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                Switch Operational Persona (Real RBAC)
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                Authenticates via backend JWT to verify actual security boundaries.
              </div>
            </div>

            {DEMO_PERSONAS.map((p) => {
              const isSelected = p.userId === activePersona?.userId;
              return (
                <div
                  key={p.userId}
                  onClick={() => handleSelect(p)}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer',
                    background: isSelected ? 'rgba(0, 242, 254, 0.08)' : 'transparent',
                    border: isSelected ? '1px solid rgba(0, 242, 254, 0.3)' : '1px solid transparent',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                    marginBottom: '4px',
                    transition: 'background var(--transition-fast)',
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) e.currentTarget.style.background = 'transparent';
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '13px', fontWeight: 700, color: isSelected ? 'var(--accent-cyan)' : 'var(--text-highlight)' }}>
                      {p.name}
                    </span>
                    <span
                      style={{
                        fontSize: '10px',
                        fontWeight: 700,
                        padding: '1px 6px',
                        borderRadius: '4px',
                        background: 'rgba(255, 255, 255, 0.08)',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      {p.role}
                    </span>
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    {p.description}
                  </span>
                </div>
              );
            })}

            {currentUser && (
              <div style={{ padding: '8px 10px', borderTop: '1px solid var(--border-subtle)', marginTop: '4px' }}>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                  ACTIVE PERMISSIONS ({currentUser.permissions?.length || 0}):
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                  {currentUser.permissions?.slice(0, 5).map((code) => (
                    <span
                      key={code}
                      style={{
                        fontSize: '9px',
                        fontFamily: 'var(--font-mono)',
                        background: 'rgba(255, 255, 255, 0.06)',
                        padding: '1px 4px',
                        borderRadius: '3px',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      {code}
                    </span>
                  ))}
                  {(currentUser.permissions?.length || 0) > 5 && (
                    <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>
                      +{currentUser.permissions.length - 5} more
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
