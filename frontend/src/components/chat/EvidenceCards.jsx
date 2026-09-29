import React from 'react';
import { formatScore } from '../../utils/formatters';

export function CitationsList({ citations }) {
  if (!citations || citations.length === 0) return null;

  return (
    <div style={{ marginTop: '10px' }}>
      <div
        style={{
          fontSize: '11px',
          fontWeight: 700,
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
          marginBottom: '6px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}
      >
        <span>📚</span>
        <span>Runbook Citations (Pinecone &ge; 0.65)</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {citations.map((c, i) => (
          <div
            key={i}
            style={{
              padding: '8px 10px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(0, 242, 254, 0.03)',
              border: '1px solid rgba(0, 242, 254, 0.15)',
              fontSize: '12px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <span style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>
                📖 {c.title || c.document_id || 'Operational Runbook'}
              </span>
              {c.similarity !== undefined && (
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '10px',
                    color: 'var(--status-healthy)',
                    background: 'rgba(16, 185, 129, 0.1)',
                    padding: '1px 5px',
                    borderRadius: '3px',
                  }}
                >
                  Score: {formatScore(c.similarity)}
                </span>
              )}
            </div>
            {c.snippet && (
              <div
                style={{
                  fontSize: '11px',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.4,
                  borderLeft: '2px solid var(--accent-cyan)',
                  paddingLeft: '6px',
                  marginTop: '4px',
                }}
              >
                {c.snippet}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export function RiskSummaryBadge({ risk }) {
  if (!risk) return null;

  const score = risk.failure_probability ?? risk.risk_score ?? 0;
  const level = risk.risk_level ?? (score >= 0.7 ? 'HIGH' : score >= 0.4 ? 'MEDIUM' : 'LOW');
  const modelType = risk.model_type || 'ML Random Forest';

  const levelColor =
    level === 'CRITICAL' || level === 'HIGH'
      ? 'var(--status-critical)'
      : level === 'MEDIUM'
      ? 'var(--status-warning)'
      : 'var(--status-healthy)';

  return (
    <div
      style={{
        marginTop: '10px',
        padding: '10px 12px',
        borderRadius: 'var(--radius-md)',
        background: 'rgba(239, 68, 68, 0.04)',
        border: `1px solid ${levelColor}40`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '8px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '16px' }}>⚠️</span>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
              Assessed Risk:
            </span>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 800,
                color: levelColor,
                background: `${levelColor}15`,
                padding: '1px 6px',
                borderRadius: '4px',
                border: `1px solid ${levelColor}50`,
              }}
            >
              {level} ({(score * 100).toFixed(0)}%)
            </span>
          </div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Model: {modelType}
          </div>
        </div>
      </div>

      {risk.explanation && (
        <div style={{ fontSize: '11px', color: 'var(--text-secondary)', maxWidth: '380px' }}>
          {risk.explanation}
        </div>
      )}
    </div>
  );
}
