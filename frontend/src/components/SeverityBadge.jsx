import React from 'react';
import { INCIDENT_SEVERITIES } from '../types/constants';

export function SeverityBadge({ severity }) {
  if (!severity) return null;
  const config = INCIDENT_SEVERITIES[severity] || { label: severity, color: 'info' };

  return (
    <span className={`badge badge-${config.color}`}>
      <span className="badge-dot" />
      {config.label}
    </span>
  );
}
