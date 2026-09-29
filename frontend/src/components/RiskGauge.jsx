import React from 'react';

export function RiskGauge({ score = 0, level = 'LOW', size = 'normal' }) {
  const percentage = Math.min(Math.max(Math.round(score * 100), 0), 100);

  let color = 'var(--status-healthy)';
  let bgGradient = 'linear-gradient(90deg, #10B981 0%, #34D399 100%)';
  if (percentage >= 70 || level === 'HIGH' || level === 'CRITICAL') {
    color = 'var(--status-critical)';
    bgGradient = 'linear-gradient(90deg, #F59E0B 0%, #EF4444 100%)';
  } else if (percentage >= 35 || level === 'MEDIUM') {
    color = 'var(--status-warning)';
    bgGradient = 'linear-gradient(90deg, #10B981 0%, #F59E0B 100%)';
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>
          Failure Risk Probability
        </span>
        <span style={{ fontSize: size === 'large' ? '18px' : '13px', fontWeight: 800, color, fontFamily: 'var(--font-mono)' }}>
          {percentage}% ({level})
        </span>
      </div>
      <div
        style={{
          width: '100%',
          height: size === 'large' ? '10px' : '6px',
          background: 'rgba(255, 255, 255, 0.08)',
          borderRadius: 'var(--radius-full)',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        <div
          style={{
            width: `${percentage}%`,
            height: '100%',
            background: bgGradient,
            borderRadius: 'var(--radius-full)',
            transition: 'width 600ms cubic-bezier(0.16, 1, 0.3, 1)',
            boxShadow: `0 0 10px ${color}`,
          }}
        />
      </div>
    </div>
  );
}
