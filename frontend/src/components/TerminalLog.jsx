import React, { useState } from 'react';

export function TerminalLog({ title = 'Execution Output', content = '', maxHeight = '280px' }) {
  const [copied, setCopied] = useState(false);

  const textToCopy = typeof content === 'object' ? JSON.stringify(content, null, 2) : String(content);

  const handleCopy = () => {
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{
      background: '#070B12',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-md)',
      overflow: 'hidden',
      fontFamily: 'var(--font-mono)',
      fontSize: '12px',
    }}>
      <div style={{
        background: '#0E1420',
        padding: '8px 14px',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#EF4444', display: 'inline-block' }} />
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#F59E0B', display: 'inline-block' }} />
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10B981', display: 'inline-block' }} />
          <span style={{ color: 'var(--text-secondary)', fontWeight: 600, marginLeft: '6px', fontSize: '11px' }}>{title}</span>
        </div>
        <button
          onClick={handleCopy}
          style={{
            color: copied ? 'var(--status-healthy)' : 'var(--text-muted)',
            fontSize: '11px',
            padding: '2px 8px',
            borderRadius: '4px',
            background: 'rgba(255, 255, 255, 0.05)',
          }}
        >
          {copied ? '✓ Copied' : 'Copy'}
        </button>
      </div>
      <div style={{
        padding: '14px',
        maxHeight,
        overflowY: 'auto',
        color: '#38BDF8',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-all',
        lineHeight: 1.6,
      }}>
        {textToCopy || '# No output logs recorded'}
      </div>
    </div>
  );
}
