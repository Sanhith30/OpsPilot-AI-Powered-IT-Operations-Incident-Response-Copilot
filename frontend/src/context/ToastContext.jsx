import React, { createContext, useContext, useState, useCallback } from 'react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info', duration = 4000) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);

    if (duration > 0) {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, duration);
    }
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}
      <div style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        maxWidth: '420px',
      }}>
        {toasts.map((t) => {
          let bg = 'var(--bg-elevated)';
          let border = 'var(--border-medium)';
          let text = 'var(--text-primary)';
          let icon = 'ℹ️';

          if (t.type === 'success') {
            bg = 'rgba(16, 185, 129, 0.9)';
            border = 'var(--status-healthy)';
            text = '#080C14';
            icon = '✅';
          } else if (t.type === 'error') {
            bg = 'rgba(239, 68, 68, 0.9)';
            border = 'var(--status-critical)';
            text = '#FFFFFF';
            icon = '⚠️';
          } else if (t.type === 'warning') {
            bg = 'rgba(245, 158, 11, 0.9)';
            border = 'var(--status-warning)';
            text = '#080C14';
            icon = '⏳';
          }

          return (
            <div
              key={t.id}
              onClick={() => removeToast(t.id)}
              style={{
                background: bg,
                border: `1px solid ${border}`,
                color: text,
                padding: '12px 18px',
                borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-lg)',
                fontSize: '13px',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                cursor: 'pointer',
                backdropFilter: 'blur(8px)',
                animation: 'toastIn 200ms ease-out',
              }}
            >
              <span>{icon}</span>
              <span style={{ flex: 1 }}>{t.message}</span>
              <span style={{ opacity: 0.7, fontSize: '10px' }}>✕</span>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
