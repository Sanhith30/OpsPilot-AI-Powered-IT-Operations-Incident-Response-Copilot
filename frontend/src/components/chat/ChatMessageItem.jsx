import React from 'react';
import { ToolTraceExpander } from './ToolTraceExpander';
import { CitationsList, RiskSummaryBadge } from './EvidenceCards';
import { formatRelativeTime } from '../../utils/formatters';

/**
 * Format simple markdown elements (bold, code, lists, headers).
 */
function renderFormattedContent(text) {
  if (!text) return null;

  // Split by code blocks first
  const parts = text.split(/(```[\s\S]*?```)/g);

  return parts.map((part, index) => {
    if (part.startsWith('```') && part.endsWith('```')) {
      const lines = part.slice(3, -3).trim().split('\n');
      const lang = lines[0].match(/^[a-zA-Z0-9_-]+$/) ? lines[0] : '';
      const code = lang ? lines.slice(1).join('\n') : lines.join('\n');

      return (
        <div key={index} style={{ margin: '8px 0', overflowX: 'auto' }}>
          <pre
            style={{
              background: '#0B0F17',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '10px 12px',
              fontFamily: 'var(--font-mono)',
              fontSize: '12px',
              color: '#38BDF8',
              lineHeight: 1.45,
              margin: 0,
            }}
          >
            <code>{code}</code>
          </pre>
        </div>
      );
    }

    // Process inline text line by line
    const lines = part.split('\n');
    return (
      <div key={index}>
        {lines.map((line, lIdx) => {
          if (!line.trim()) {
            return <div key={lIdx} style={{ height: '8px' }} />;
          }

          // Bullet points
          if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
            const bulletText = line.trim().slice(2);
            return (
              <div key={lIdx} style={{ display: 'flex', gap: '8px', marginLeft: '8px', marginY: '3px' }}>
                <span style={{ color: 'var(--accent-cyan)' }}>•</span>
                <span>{renderInlineStyles(bulletText)}</span>
              </div>
            );
          }

          // Numbered lists
          const numMatch = line.trim().match(/^(\d+)\.\s+(.*)/);
          if (numMatch) {
            return (
              <div key={lIdx} style={{ display: 'flex', gap: '8px', marginLeft: '8px', marginY: '3px' }}>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)', fontWeight: 600 }}>
                  {numMatch[1]}.
                </span>
                <span>{renderInlineStyles(numMatch[2])}</span>
              </div>
            );
          }

          // Headers
          if (line.startsWith('### ')) {
            return (
              <h4 key={lIdx} style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-highlight)', margin: '8px 0 4px' }}>
                {line.slice(4)}
              </h4>
            );
          }
          if (line.startsWith('## ')) {
            return (
              <h3 key={lIdx} style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-highlight)', margin: '10px 0 4px' }}>
                {line.slice(3)}
              </h3>
            );
          }

          return (
            <p key={lIdx} style={{ margin: '3px 0' }}>
              {renderInlineStyles(line)}
            </p>
          );
        })}
      </div>
    );
  });
}

/**
 * Handle inline **bold** and `code`.
 */
function renderInlineStyles(text) {
  // Split on bold or inline code
  const tokens = text.split(/(\*\*.*?\*\*|`.*?`)/g);

  return tokens.map((token, i) => {
    if (token.startsWith('**') && token.endsWith('**')) {
      return (
        <strong key={i} style={{ color: 'var(--text-highlight)', fontWeight: 700 }}>
          {token.slice(2, -2)}
        </strong>
      );
    }
    if (token.startsWith('`') && token.endsWith('`')) {
      return (
        <code
          key={i}
          style={{
            background: 'rgba(0, 242, 254, 0.08)',
            color: 'var(--accent-cyan)',
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            padding: '2px 5px',
            borderRadius: '4px',
            border: '1px solid rgba(0, 242, 254, 0.2)',
          }}
        >
          {token.slice(1, -1)}
        </code>
      );
    }
    return token;
  });
}

export function ChatMessageItem({ message, onFollowUpClick }) {
  const isUser = message.role === 'user';

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '18px',
        width: '100%',
      }}
    >
      {/* Header with avatar / name */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '5px',
          fontSize: '11px',
          color: 'var(--text-muted)',
          flexDirection: isUser ? 'row-reverse' : 'row',
        }}
      >
        <div
          style={{
            width: '24px',
            height: '24px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '11px',
            background: isUser
              ? 'linear-gradient(135deg, #1E293B 0%, #334155 100%)'
              : 'linear-gradient(135deg, #00F2FE 0%, #0284C7 100%)',
            color: isUser ? '#E2E8F0' : '#080C14',
            boxShadow: isUser ? 'none' : '0 0 10px rgba(0, 242, 254, 0.4)',
            fontWeight: 700,
          }}
        >
          {isUser ? '👤' : '🤖'}
        </div>
        <span style={{ fontWeight: 600, color: isUser ? 'var(--text-secondary)' : 'var(--accent-cyan)' }}>
          {isUser ? 'You' : 'OpsPilot Copilot'}
        </span>
        {message.created_at && (
          <span style={{ fontSize: '10px' }}>
            • {formatRelativeTime(message.created_at)}
          </span>
        )}
      </div>

      {/* Bubble Container */}
      <div
        style={{
          maxWidth: '85%',
          background: isUser
            ? 'linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%)'
            : 'var(--bg-elevated)',
          border: isUser
            ? '1px solid rgba(56, 189, 248, 0.25)'
            : '1px solid var(--border-subtle)',
          borderRadius: isUser ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
          padding: '14px 16px',
          boxShadow: isUser ? 'var(--shadow-sm)' : 'var(--shadow-md)',
          color: 'var(--text-primary)',
          fontSize: '13px',
          lineHeight: 1.55,
        }}
      >
        {/* Render text */}
        <div style={{ wordBreak: 'break-word' }}>
          {renderFormattedContent(message.content)}
        </div>

        {/* Tool trace if available */}
        {message.tool_trace && message.tool_trace.length > 0 && (
          <ToolTraceExpander toolTrace={message.tool_trace} />
        )}

        {/* Citations if available */}
        {message.citations && message.citations.length > 0 && (
          <CitationsList citations={message.citations} />
        )}

        {/* Risk summary if available */}
        {message.risk && (
          <RiskSummaryBadge risk={message.risk} />
        )}
      </div>
    </div>
  );
}
