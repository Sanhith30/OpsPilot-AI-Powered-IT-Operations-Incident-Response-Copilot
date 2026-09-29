import React, { useEffect, useState } from 'react';
import { getIncidents } from '../api/incidents';
import { StatusBadge } from '../components/StatusBadge';
import { SeverityBadge } from '../components/SeverityBadge';
import { formatDate, formatRelativeTime } from '../utils/formatters';

export function IncidentsPage({ onSelectIncident }) {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const loadIncidents = async () => {
    try {
      setLoading(true);
      const data = await getIncidents();
      setIncidents(data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to fetch incidents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIncidents();
  }, []);

  const filtered = incidents.filter((inc) => {
    if (statusFilter !== 'ALL' && inc.status !== statusFilter) return false;
    if (severityFilter !== 'ALL' && inc.severity !== severityFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = (inc.title || '').toLowerCase().includes(q);
      const matchDesc = (inc.description || '').toLowerCase().includes(q);
      const matchId = String(inc.incident_id).includes(q);
      if (!matchTitle && !matchDesc && !matchId) return false;
    }
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <span>Incident Queue &amp; Triage</span>
          </h1>
          <p className="page-subtitle">
            Real-time incident stream tracked in PostgreSQL with automated correlation &amp; escalation.
          </p>
        </div>
        <button className="btn btn-secondary" onClick={loadIncidents}>
          Refresh
        </button>
      </div>

      {/* Filter Bar */}
      <div
        className="card"
        style={{
          padding: '16px 20px',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '16px',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
          <input
            type="text"
            placeholder="Search by title, description or #ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-medium)',
              borderRadius: 'var(--radius-md)',
              padding: '8px 14px',
              width: '280px',
              fontSize: '13px',
              color: 'var(--text-primary)',
            }}
          />

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-medium)',
                borderRadius: 'var(--radius-md)',
                padding: '8px 12px',
                fontSize: '13px',
                color: 'var(--text-primary)',
              }}
            >
              <option value="ALL">All Statuses</option>
              <option value="OPEN">Open</option>
              <option value="INVESTIGATING">Investigating</option>
              <option value="MITIGATED">Mitigated</option>
              <option value="RESOLVED">Resolved</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-medium)',
                borderRadius: 'var(--radius-md)',
                padding: '8px 12px',
                fontSize: '13px',
                color: 'var(--text-primary)',
              }}
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical (P1)</option>
              <option value="HIGH">High (P2)</option>
              <option value="MEDIUM">Medium (P3)</option>
              <option value="LOW">Low (P4)</option>
            </select>
          </div>
        </div>

        <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          Showing <strong>{filtered.length}</strong> of {incidents.length} incidents
        </div>
      </div>

      {/* Incidents Table */}
      <div className="table-container">
        {loading && incidents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
            <div className="spinner" style={{ marginBottom: '12px' }} />
            <div>Loading incidents from database...</div>
          </div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--status-critical)' }}>
            {error}
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
            No incidents matched your filter criteria.
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: '80px' }}>ID</th>
                <th>Incident Title</th>
                <th style={{ width: '130px' }}>Severity</th>
                <th style={{ width: '130px' }}>Status</th>
                <th style={{ width: '140px' }}>Reported</th>
                <th style={{ width: '110px', textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((inc) => (
                <tr
                  key={inc.incident_id}
                  onClick={() => onSelectIncident(inc.incident_id)}
                  style={{ cursor: 'pointer' }}
                >
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                    #{inc.incident_id}
                  </td>
                  <td>
                    <div style={{ fontWeight: 600, color: 'var(--text-highlight)', marginBottom: '3px' }}>
                      {inc.title}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', maxWidth: '600px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {inc.description || 'No detailed description'}
                    </div>
                  </td>
                  <td>
                    <SeverityBadge severity={inc.severity} />
                  </td>
                  <td>
                    <StatusBadge status={inc.status} />
                  </td>
                  <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    {formatRelativeTime(inc.created_at)}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      className="btn btn-primary"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectIncident(inc.incident_id);
                      }}
                      style={{ fontSize: '11px', padding: '5px 10px' }}
                    >
                      Investigate &rarr;
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
