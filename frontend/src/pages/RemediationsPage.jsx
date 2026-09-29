import React, { useEffect, useState } from 'react';
import {
  getIncidentRemediations,
  approveRemediation,
  rejectRemediation,
  executeRemediation,
  verifyRemediation,
} from '../api/remediations';
import { getIncidents } from '../api/incidents';
import { StatusBadge } from '../components/StatusBadge';
import { TerminalLog } from '../components/TerminalLog';
import { Modal } from '../components/Modal';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { formatDate, formatRelativeTime } from '../utils/formatters';

export function RemediationsPage({ onNavigateToIncident }) {
  const { hasPermission, currentUser, activePersona } = useAuth();
  const { addToast } = useToast();

  const [remediations, setRemediations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedIncidentId, setSelectedIncidentId] = useState(1);
  const [allIncidents, setAllIncidents] = useState([]);

  // Review Dialog State
  const [reviewModal, setReviewModal] = useState({
    isOpen: false,
    remediationId: null,
    decision: 'APPROVE', // 'APPROVE', 'REJECT', 'REQUEST_MORE_INFO'
    comment: '',
    submitting: false,
  });

  // Execution & Verification State
  const [dryRunMap, setDryRunMap] = useState({});
  const [actionLoading, setActionLoading] = useState({});

  const loadData = async () => {
    try {
      setLoading(true);
      const [incs, rems] = await Promise.all([
        getIncidents().catch(() => []),
        getIncidentRemediations(selectedIncidentId).catch(() => []),
      ]);
      setAllIncidents(incs);
      setRemediations(rems);
    } catch (err) {
      addToast(`Error loading remediations: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedIncidentId]);

  const handleOpenReview = (remId, decision) => {
    if (!hasPermission('ACTION_APPROVE')) {
      addToast('RBAC Restricted: ACTION_APPROVE permission required (Manager or Admin).', 'error');
      return;
    }
    setReviewModal({
      isOpen: true,
      remediationId: remId,
      decision,
      comment: decision === 'APPROVE' ? 'Approved by operational authority' : '',
      submitting: false,
    });
  };

  const handleConfirmReview = async () => {
    const { remediationId, decision, comment } = reviewModal;
    setReviewModal((prev) => ({ ...prev, submitting: true }));

    try {
      if (decision === 'APPROVE') {
        await approveRemediation(remediationId, decision, comment);
        addToast(`Remediation #${remediationId} APPROVED! Ready for execution.`, 'success');
      } else if (decision === 'REJECT') {
        await rejectRemediation(remediationId, decision, comment);
        addToast(`Remediation #${remediationId} REJECTED.`, 'warning');
      } else {
        await approveRemediation(remediationId, 'REQUEST_MORE_INFO', comment);
        addToast(`Remediation #${remediationId} status updated to REQUEST_MORE_INFO.`, 'info');
      }

      setReviewModal({ isOpen: false, remediationId: null, decision: 'APPROVE', comment: '', submitting: false });
      const updated = await getIncidentRemediations(selectedIncidentId);
      setRemediations(updated);
    } catch (err) {
      addToast(`Review error: ${err.message}`, 'error');
      setReviewModal((prev) => ({ ...prev, submitting: false }));
    }
  };

  const handleExecute = async (remId) => {
    if (!hasPermission('ACTION_APPROVE')) {
      addToast('RBAC Restricted: Execution requires ACTION_APPROVE permission (Manager or Admin).', 'error');
      return;
    }

    const isDryRun = dryRunMap[remId] !== false; // default true
    setActionLoading((prev) => ({ ...prev, [remId]: 'executing' }));

    try {
      const res = await executeRemediation(remId, isDryRun);
      addToast(`Execution finished! Status: ${res.status}`, res.status === 'COMPLETED' ? 'success' : 'error');
      const updated = await getIncidentRemediations(selectedIncidentId);
      setRemediations(updated);
    } catch (err) {
      if (err.status === 409) {
        addToast(`Idempotency Conflict: ${err.message}`, 'warning');
      } else {
        addToast(`Execution Failed: ${err.message}`, 'error');
      }
      const updated = await getIncidentRemediations(selectedIncidentId);
      setRemediations(updated);
    } finally {
      setActionLoading((prev) => ({ ...prev, [remId]: null }));
    }
  };

  const handleVerify = async (remId, forceFail = false) => {
    if (!hasPermission('ACTION_REQUEST')) {
      addToast('RBAC Restricted: Verification requires ACTION_REQUEST permission (L2, Manager, or Admin).', 'error');
      return;
    }

    setActionLoading((prev) => ({ ...prev, [remId]: 'verifying' }));

    try {
      const res = await verifyRemediation(remId, forceFail);
      if (res.status === 'VERIFIED') {
        addToast(`Health Probes PASSED! Incident #${selectedIncidentId} updated to MITIGATED.`, 'success');
      } else {
        addToast(`Health Probes FAILED! Status: ${res.status}`, 'error');
      }
      const updated = await getIncidentRemediations(selectedIncidentId);
      setRemediations(updated);
    } catch (err) {
      addToast(`Verification Error: ${err.message}`, 'error');
    } finally {
      setActionLoading((prev) => ({ ...prev, [remId]: null }));
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <span>Human Approval &amp; Remediation Lifecycle</span>
          </h1>
          <p className="page-subtitle">
            Screens 8 &amp; 9: Strict state machine transitions, idempotent execution locks, safe whitelisted adapters &amp; automated post-verification probes.
          </p>
        </div>

        {/* Incident Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Incident:</span>
          <select
            value={selectedIncidentId}
            onChange={(e) => setSelectedIncidentId(Number(e.target.value))}
            style={{
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-medium)',
              borderRadius: 'var(--radius-md)',
              padding: '6px 12px',
              fontSize: '13px',
              color: 'var(--text-primary)',
            }}
          >
            {allIncidents.map((inc) => (
              <option key={inc.incident_id} value={inc.incident_id}>
                #{inc.incident_id}: {inc.title}
              </option>
            ))}
          </select>
          <button className="btn btn-secondary" onClick={loadData}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* RBAC Notice Banner */}
      <div
        className="card"
        style={{
          background: 'rgba(0, 242, 254, 0.05)',
          borderColor: 'rgba(0, 242, 254, 0.25)',
          padding: '12px 18px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '16px' }}>🛡️</span>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Logged in as <strong>{activePersona.name} ({activePersona.role})</strong>.
            {hasPermission('ACTION_APPROVE') ? (
              <span style={{ color: 'var(--status-healthy)', marginLeft: '6px', fontWeight: 600 }}>
                • You have ACTION_APPROVE permission (Can approve &amp; execute).
              </span>
            ) : hasPermission('ACTION_REQUEST') ? (
              <span style={{ color: 'var(--status-warning)', marginLeft: '6px', fontWeight: 600 }}>
                • You have ACTION_REQUEST permission (Can request &amp; verify; cannot approve).
              </span>
            ) : (
              <span style={{ color: 'var(--status-critical)', marginLeft: '6px', fontWeight: 600 }}>
                • Read-only access (L1 Engineer; approval/execution buttons disabled).
              </span>
            )}
          </div>
        </div>

        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          State Machine: PENDING &rarr; APPROVED &rarr; EXECUTING &rarr; COMPLETED &rarr; VERIFIED
        </span>
      </div>

      {/* Remediations List */}
      {loading && remediations.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
          <div className="spinner" style={{ marginBottom: '12px' }} />
          <div>Loading remediations from database...</div>
        </div>
      ) : remediations.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
          <h3>No remediation actions recorded for Incident #{selectedIncidentId}.</h3>
          <p style={{ marginTop: '8px', fontSize: '13px' }}>
            Go to the Incident Detail page to synthesize AI intelligence and request a recommended action.
          </p>
          <button
            className="btn btn-primary"
            onClick={() => onNavigateToIncident(selectedIncidentId)}
            style={{ marginTop: '16px' }}
          >
            Open Incident Details &rarr;
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {remediations.map((rem) => {
            const isExecuting = actionLoading[rem.remediation_id] === 'executing';
            const isVerifying = actionLoading[rem.remediation_id] === 'verifying';
            const isDryRun = dryRunMap[rem.remediation_id] !== false;

            return (
              <div
                key={rem.remediation_id}
                className="card-elevated"
                style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}
              >
                {/* Header Row */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-cyan)', fontSize: '14px' }}>
                        {rem.action_id}
                      </span>
                      <span style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-highlight)' }}>
                        {rem.title}
                      </span>
                      <StatusBadge status={rem.status} type="remediation" />
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                      Adapter: <code>{rem.action_type}</code> • Requested by User #{rem.requested_by_user_id} {formatRelativeTime(rem.created_at)}
                    </div>
                  </div>

                  {/* Actions Bar according to State Machine */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    {/* Stage 1: PENDING_APPROVAL -> APPROVE / REJECT */}
                    {rem.status === 'PENDING_APPROVAL' && (
                      <>
                        <button
                          className="btn btn-success"
                          onClick={() => handleOpenReview(rem.remediation_id, 'APPROVE')}
                          disabled={!hasPermission('ACTION_APPROVE')}
                          title={!hasPermission('ACTION_APPROVE') ? 'Requires ACTION_APPROVE permission (Manager/Admin)' : 'Approve remediation'}
                        >
                          ✓ Approve Action
                        </button>
                        <button
                          className="btn btn-danger"
                          onClick={() => handleOpenReview(rem.remediation_id, 'REJECT')}
                          disabled={!hasPermission('ACTION_APPROVE')}
                        >
                          ✕ Reject
                        </button>
                        <button
                          className="btn btn-secondary"
                          onClick={() => handleOpenReview(rem.remediation_id, 'REQUEST_MORE_INFO')}
                          disabled={!hasPermission('ACTION_APPROVE')}
                        >
                          ? More Info
                        </button>
                      </>
                    )}

                    {/* Stage 2: APPROVED -> EXECUTE */}
                    {rem.status === 'APPROVED' && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={isDryRun}
                            onChange={(e) => setDryRunMap((prev) => ({ ...prev, [rem.remediation_id]: e.target.checked }))}
                          />
                          <span>Safe Dry-Run Mode</span>
                        </label>
                        <button
                          className="btn btn-primary"
                          onClick={() => handleExecute(rem.remediation_id)}
                          disabled={isExecuting || !hasPermission('ACTION_APPROVE')}
                          title={!hasPermission('ACTION_APPROVE') ? 'Requires ACTION_APPROVE permission (Manager/Admin)' : 'Execute via registered adapter'}
                        >
                          {isExecuting ? <><span className="spinner" /> Executing...</> : '⚡ Claim & Execute'}
                        </button>
                      </div>
                    )}

                    {/* Stage 3: COMPLETED -> VERIFY */}
                    {rem.status === 'COMPLETED' && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <button
                          className="btn btn-success"
                          onClick={() => handleVerify(rem.remediation_id, false)}
                          disabled={isVerifying || !hasPermission('ACTION_REQUEST')}
                          title={!hasPermission('ACTION_REQUEST') ? 'Requires ACTION_REQUEST permission (L2/Manager/Admin)' : 'Run automated verification'}
                        >
                          {isVerifying ? <><span className="spinner" /> Verifying Probes...</> : '🛡️ Run Automated Health Verification'}
                        </button>
                        <button
                          className="btn btn-ghost"
                          onClick={() => handleVerify(rem.remediation_id, true)}
                          disabled={isVerifying || !hasPermission('ACTION_REQUEST')}
                          style={{ fontSize: '11px', color: 'var(--status-critical)' }}
                          title="Simulate probe failure to test VERIFICATION_FAILED branch"
                        >
                          (Test Fail Branch)
                        </button>
                      </div>
                    )}

                    {/* Stage 4: VERIFIED -> Success state */}
                    {rem.status === 'VERIFIED' && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--status-healthy)', fontWeight: 700, fontSize: '13px' }}>
                        <span>🛡️ Verified Safe • Incident Mitigated</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Details & Rationale */}
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  <strong>Operational Rationale:</strong> {rem.rationale || 'N/A'}
                </div>

                {/* Payload & Execution Terminal Output */}
                <div className="grid-2">
                  <div>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                      EXECUTION PAYLOAD (Whitelisted Parameters)
                    </span>
                    <TerminalLog title="Payload Config" content={rem.execution_payload || {}} maxHeight="140px" />
                  </div>

                  <div>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                      ADAPTER EXECUTION LOGS &amp; TELEMETRY
                    </span>
                    <TerminalLog
                      title={rem.execution_result ? `Output (${rem.status})` : 'Awaiting Execution'}
                      content={rem.execution_result || '# Execution has not been triggered yet'}
                      maxHeight="140px"
                    />
                  </div>
                </div>

                {/* Verification Results Panel */}
                {rem.verification_result && (
                  <div
                    style={{
                      background: rem.status === 'VERIFIED' ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
                      border: `1px solid ${rem.status === 'VERIFIED' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                      borderRadius: 'var(--radius-md)',
                      padding: '12px 16px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <strong style={{ color: rem.status === 'VERIFIED' ? 'var(--status-healthy)' : 'var(--status-critical)' }}>
                        {rem.status === 'VERIFIED' ? '✓ Automated Verification Probes Succeeded' : '✕ Verification Probes Detected Anomalies'}
                      </strong>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        Verified at {formatDate(rem.verified_at)}
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                      Probe message: {rem.verification_result.details?.message || rem.verification_result.message || 'Health probe executed successfully.'}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Human Approval Review Modal (Screen 8) */}
      <Modal
        isOpen={reviewModal.isOpen}
        onClose={() => setReviewModal((prev) => ({ ...prev, isOpen: false }))}
        title={`Human Review Gate: ${reviewModal.decision}`}
        footer={
          <>
            <button
              className="btn btn-secondary"
              onClick={() => setReviewModal((prev) => ({ ...prev, isOpen: false }))}
            >
              Cancel
            </button>
            <button
              className={`btn ${reviewModal.decision === 'APPROVE' ? 'btn-success' : 'btn-danger'}`}
              onClick={handleConfirmReview}
              disabled={reviewModal.submitting}
            >
              {reviewModal.submitting ? 'Submitting...' : `Confirm ${reviewModal.decision}`}
            </button>
          </>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            You are reviewing remediation action <strong>#{reviewModal.remediationId}</strong> as{' '}
            <strong style={{ color: 'var(--accent-cyan)' }}>{activePersona.name} ({activePersona.role})</strong>.
          </div>

          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
              Review Rationale / Comment:
            </label>
            <textarea
              rows={3}
              value={reviewModal.comment}
              onChange={(e) => setReviewModal((prev) => ({ ...prev, comment: e.target.value }))}
              placeholder="Enter review decision notes..."
              style={{
                width: '100%',
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-medium)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-primary)',
                padding: '10px',
                fontSize: '13px',
              }}
            />
          </div>

          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            This action will be permanently recorded in the immutable audit log with your user ID and cryptographic timestamp.
          </div>
        </div>
      </Modal>
    </div>
  );
}
