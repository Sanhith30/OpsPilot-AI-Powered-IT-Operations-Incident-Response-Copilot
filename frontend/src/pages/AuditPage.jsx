import React, { useEffect, useState } from 'react';
import { getAuditLogs } from '../api/audit';
import { formatDate, formatRelativeTime } from '../utils/formatters';

export function AuditPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [resourceFilter, setResourceFilter] = useState('ALL');

  const loadLogs = async () => {
    try {
      setLoading(true);
      const resType = resourceFilter === 'ALL' ? null : resourceFilter;
      const data = await getAuditLogs(100, resType);
      setLogs(data);
    } catch (err) {
      console.error('Audit fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, [resourceFilter]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <span>Immutable Audit Trail &amp; Observability</span>
          </h1>
          <p className="page-subtitle">
            Screen 10: Cryptographically logged operations, human approvals, execution claims, and OpenTelemetry trace correlations.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <a
            href="/metrics"
            target="_blank"
            rel="noreferrer"
            className="btn btn-secondary"
            title="Open Prometheus raw metrics endpoint"
          >
            📊 Prometheus Metrics &nearr;
          </a>
          <button className="btn btn-secondary" onClick={loadLogs}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="card" style={{ padding: '14px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Resource Filter:</span>
          <select
            value={resourceFilter}
            onChange={(e) => setResourceFilter(e.target.value)}
            style={{
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-medium)',
              borderRadius: 'var(--radius-md)',
              padding: '6px 12px',
              fontSize: '13px',
              color: 'var(--text-primary)',
            }}
          >
            <option value="ALL">All Resource Types</option>
            <option value="REMEDIATION_ACTION">REMEDIATION_ACTION</option>
            <option value="INCIDENT">INCIDENT</option>
            <option value="INVESTIGATION">INVESTIGATION</option>
          </select>
        </div>

        <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          Showing <strong>{logs.length}</strong> immutable audit events
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="table-container">
        {loading && logs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
            <div className="spinner" style={{ marginBottom: '12px' }} />
            <div>Loading audit records from PostgreSQL core.audit_logs...</div>
          </div>
        ) : logs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>
            No audit records found matching criteria.
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: '80px' }}>ID</th>
                <th style={{ width: '150px' }}>Timestamp</th>
                <th style={{ width: '220px' }}>Action</th>
                <th style={{ width: '90px' }}>Actor</th>
                <th style={{ width: '180px' }}>Resource</th>
                <th style={{ width: '90px' }}>Result</th>
                <th>Request / Trace ID &amp; Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => {
                const isSuccess = log.action_result === 'SUCCESS';
                return (
                  <tr key={log.audit_id}>
                    <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                      #{log.audit_id}
                    </td>
                    <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                      {formatDate(log.created_at)}
                    </td>
                    <td>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '12px', color: 'var(--text-highlight)' }}>
                        {log.action}
                      </span>
                    </td>
                    <td style={{ fontSize: '12px' }}>
                      User #{log.actor_user_id || 'System'}
                    </td>
                    <td>
                      <span className="badge badge-info" style={{ fontSize: '10px' }}>
                        {log.resource_type}: #{log.resource_id}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${isSuccess ? 'badge-healthy' : 'badge-critical'}`} style={{ fontSize: '10px' }}>
                        {log.action_result}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        {log.request_id && (
                          <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--accent-blue)' }}>
                            Trace: {log.request_id}
                          </span>
                        )}
                        {log.details && (
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)', maxWidth: '400px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {JSON.stringify(log.details)}
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
