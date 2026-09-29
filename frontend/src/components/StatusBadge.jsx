import React from 'react';
import { INCIDENT_STATUSES, REMEDIATION_STATUSES } from '../types/constants';

export function StatusBadge({ status, type = 'incident' }) {
  if (!status) return null;

  const dict = type === 'remediation' ? REMEDIATION_STATUSES : INCIDENT_STATUSES;
  const config = dict[status] || { label: status, color: 'info' };

  return (
    <span className={`badge badge-${config.color}`}>
      <span className="badge-dot" />
      {config.icon && <span style={{ marginRight: '2px' }}>{config.icon}</span>}
      {config.label}
    </span>
  );
}
