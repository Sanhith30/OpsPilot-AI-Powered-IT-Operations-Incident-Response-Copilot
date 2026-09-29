import React, { useEffect, useState } from 'react';
import { getDashboardSummary } from '../api/dashboard';
import { StatusBadge } from '../components/StatusBadge';
import { SeverityBadge } from '../components/SeverityBadge';
import { formatDate, formatRelativeTime } from '../utils/formatters';

export function DashboardPage({ onNavigateToIncident, onNavigateToTab }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSummary = async () => {
    try {
      setLoading(true);
      const res = await getDashboardSummary();
      setData(res);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to fetch dashboard summary');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
    const interval = setInterval(fetchSummary, 15000); // 15s refresh
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0', color: 'var(--text-muted)' }}>
        <div className="spinner" style={{ width: '32px', height: '32px', marginBottom: '16px' }} />
        <div>Connecting to OpsPilot Intelligence Engine...</div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="card" style={{ borderColor: 'var(--status-critical)', padding: '32px', textAlign: 'center' }}>
        <h3 style={{ color: 'var(--status-critical)', marginBottom: '8px' }}>Dashboard Offline</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>{error}</p>
        <button className="btn btn-secondary" onClick={fetchSummary}>Retry Connection</button>
      </div>
    );
  }

  const kpis = data?.kpis || {};
  const services = data?.services || [];
  const alerts = data?.recent_alerts || [];
  const remediations = data?.recent_remediations || [];
  const activeIncidents = data?.active_incidents_list || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <span>Operations Cockpit</span>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--accent-cyan)' }}>
              • Live Telemetry &amp; Autonomous Remediation
            </span>
          </h1>
          <p className="page-subtitle">
            Continuous fleet monitoring, root-cause correlation, and human-approved remediation lifecycle.
          </p>
        </div>
        <button className="btn btn-secondary" onClick={fetchSummary} title="Refresh real data">
          <span>🔄</span> Refresh
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid-4">
        <div className="stat-card cyan">
          <span className="stat-label">Active Incidents</span>
          <span className="stat-value">{kpis.active_incidents ?? 0}</span>
          <span className="stat-subtext">
            {kpis.critical_incidents > 0 ? (
              <span style={{ color: 'var(--status-critical)', fontWeight: 700 }}>
                {kpis.critical_incidents} Critical (P1)
              </span>
            ) : (
              <span style={{ color: 'var(--status-healthy)' }}>No Critical P1 Active</span>
            )}
          </span>
        </div>

        <div className="stat-card warning">
          <span className="stat-label">Pending Human Approvals</span>
          <span className="stat-value">{kpis.pending_approvals ?? 0}</span>
          <span className="stat-subtext">
            {kpis.pending_approvals > 0 ? (
              <span style={{ color: 'var(--status-warning)', fontWeight: 700 }}>Requires SRE / Manager review</span>
            ) : (
              'All proposed actions reviewed'
            )}
          </span>
        </div>

        <div className="stat-card healthy">
          <span className="stat-label">Verified Safe Remediations</span>
          <span className="stat-value">{kpis.verified_remediations ?? 0}</span>
          <span className="stat-subtext">Automated health checks passed</span>
        </div>

        <div className="stat-card cyan">
          <span className="stat-label">Mean Time to Detect (MTTD)</span>
          <span className="stat-value">{kpis.mttd_minutes}m</span>
          <span className="stat-subtext">AI correlation speed: &lt; 4 mins</span>
        </div>
      </div>

      {/* Main 2-column layout */}
      <div className="grid-2">
        {/* Left Column: Monitored Services Grid & Active Incidents */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Monitored Services */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-highlight)' }}>
                Monitored Service Fleet
              </h2>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Fleet Health: <strong style={{ color: 'var(--status-healthy)' }}>{kpis.fleet_health_score}%</strong>
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {services.map((svc) => {
                let badgeClass = 'badge-healthy';
                let statusLabel = 'HEALTHY';
                if (svc.status === 'CRITICAL') {
                  badgeClass = 'badge-critical';
                  statusLabel = 'CRITICAL IMPACT';
                } else if (svc.status === 'DEGRADED') {
                  badgeClass = 'badge-warning';
                  statusLabel = 'DEGRADED';
                }

                return (
                  <div
                    key={svc.service_id}
                    style={{
                      background: 'var(--bg-elevated)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-md)',
                      padding: '12px 16px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-highlight)' }}>
                          {svc.name}
                        </span>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>({svc.tier})</span>
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        Environment: {svc.env} • Active alerts: {svc.active_incident_count}
                      </div>
                    </div>
                    <span className={`badge ${badgeClass}`}>{statusLabel}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Active Incidents Quick List */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-highlight)' }}>
                Active Incident Queue
              </h2>
              <button
                className="btn btn-ghost"
                onClick={() => onNavigateToTab('incidents')}
                style={{ fontSize: '12px', padding: '4px 8px' }}
              >
                View All &rarr;
              </button>
            </div>

            {activeIncidents.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-muted)' }}>
                No active incidents currently reported in queue.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {activeIncidents.map((inc) => (
                  <div
                    key={inc.incident_id}
                    onClick={() => onNavigateToIncident(inc.incident_id)}
                    style={{
                      background: 'var(--bg-elevated)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-md)',
                      padding: '12px 14px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      cursor: 'pointer',
                      transition: 'border-color var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-cyan)')}
                    onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-subtle)')}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--accent-cyan)' }}>
                          #{inc.incident_id}
                        </span>
                        <span style={{ fontWeight: 600, color: 'var(--text-highlight)' }}>{inc.title}</span>
                      </div>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        Created {formatRelativeTime(inc.created_at)}
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <SeverityBadge severity={inc.severity} />
                      <StatusBadge status={inc.status} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Recent Remediation Lifecycle & Alert Stream */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Recent Remediations */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-highlight)' }}>
                Remediation Lifecycle Stream
              </h2>
              <button
                className="btn btn-ghost"
                onClick={() => onNavigateToTab('remediations')}
                style={{ fontSize: '12px', padding: '4px 8px' }}
              >
                Manage &rarr;
              </button>
            </div>

            {remediations.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-muted)' }}>
                No remediation actions currently submitted.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {remediations.map((rem) => (
                  <div
                    key={rem.remediation_id}
                    onClick={() => onNavigateToTab('remediations')}
                    style={{
                      background: 'var(--bg-elevated)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-md)',
                      padding: '12px 14px',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                      <div>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--accent-cyan)', marginRight: '6px' }}>
                          {rem.action_id}
                        </span>
                        <span style={{ fontWeight: 600, color: 'var(--text-highlight)' }}>{rem.title}</span>
                      </div>
                      <StatusBadge status={rem.status} type="remediation" />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
                      <span>Action: <code>{rem.action_type}</code></span>
                      <span>{formatRelativeTime(rem.created_at)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Operational Alerts / Events Feed */}
          <div className="card">
            <h2 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-highlight)', marginBottom: '16px' }}>
              Live Telemetry &amp; Detection Events
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '340px', overflowY: 'auto' }}>
              {alerts.map((al) => (
                <div
                  key={al.event_id}
                  style={{
                    background: '#0B0F17',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '8px 12px',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '10px',
                    fontSize: '12px',
                  }}
                >
                  <span style={{ fontSize: '14px' }}>
                    {al.type === 'DEPLOYMENT_DETECTED' ? '🚀' :
                     al.type === 'METRIC_THRESHOLD_EXCEEDED' ? '📈' :
                     al.type === 'LOG_ANOMALY_DETECTED' ? '🔍' :
                     al.type === 'MITIGATION_APPLIED' ? '🛡️' : '🚨'}
                  </span>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                      <strong style={{ color: 'var(--text-highlight)', fontSize: '11px' }}>{al.type}</strong>
                      <span style={{ color: 'var(--text-muted)', fontSize: '10px' }}>{formatRelativeTime(al.timestamp)}</span>
                    </div>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>{al.description}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
