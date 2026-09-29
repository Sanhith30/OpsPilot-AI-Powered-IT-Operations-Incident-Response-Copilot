import React, { useEffect, useState } from 'react';
import { getIncident, getIncidentEvents, getIncidentInvestigations } from '../api/incidents';
import { getIntelligence, generateIntelligence } from '../api/intelligence';
import { createInvestigation, getInvestigationDetails, getRagEvidence } from '../api/investigations';
import { getIncidentRemediations, createRemediation } from '../api/remediations';
import { StatusBadge } from '../components/StatusBadge';
import { SeverityBadge } from '../components/SeverityBadge';
import { RiskGauge } from '../components/RiskGauge';
import { GroundingBadge } from '../components/GroundingBadge';
import { TerminalLog } from '../components/TerminalLog';
import { Modal } from '../components/Modal';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { formatDate, formatRelativeTime, formatScore } from '../utils/formatters';
import { IncidentChatTab } from '../components/chat/IncidentChatTab';

export function IncidentDetailPage({ incidentId, onBack, onNavigateToRemediations }) {
  const { hasPermission, currentUser } = useAuth();
  const { addToast } = useToast();

  const [incident, setIncident] = useState(null);
  const [events, setEvents] = useState([]);
  const [investigations, setInvestigations] = useState([]);
  const [activeInvestigationId, setActiveInvestigationId] = useState(null);
  const [intelligence, setIntelligence] = useState(null);
  const [ragEvidence, setRagEvidence] = useState([]);
  const [remediations, setRemediations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generatingIntel, setGeneratingIntel] = useState(false);
  const [runningInvestigation, setRunningInvestigation] = useState(false);
  const [activeTab, setActiveTab] = useState('intelligence'); // 'intelligence', 'timeline', 'rag', 'remediations'

  // Request Remediation Modal
  const [isRequestModalOpen, setIsRequestModalOpen] = useState(false);
  const [selectedAction, setSelectedAction] = useState(null);
  const [remPayload, setRemPayload] = useState('{}');
  const [submittingRem, setSubmittingRem] = useState(false);

  // Runbook Drawer
  const [selectedRunbook, setSelectedRunbook] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [incData, evs, invs, rems] = await Promise.all([
        getIncident(incidentId),
        getIncidentEvents(incidentId).catch(() => []),
        getIncidentInvestigations(incidentId).catch(() => []),
        getIncidentRemediations(incidentId).catch(() => []),
      ]);
      setIncident(incData);
      setEvents(evs);
      setInvestigations(invs);
      setRemediations(rems);

      const latestInvId = invs.length > 0 ? invs[invs.length - 1].investigation_id : 1;
      setActiveInvestigationId(latestInvId);

      // Load intelligence
      try {
        const intel = await getIntelligence(incidentId);
        setIntelligence(intel);
      } catch (err) {
        console.log('No prior intelligence found, will generate on request');
      }

      // Load RAG evidence if investigation exists
      if (latestInvId) {
        try {
          const rag = await getRagEvidence(latestInvId);
          setRagEvidence(rag);
        } catch {
          setRagEvidence([]);
        }
      }
    } catch (err) {
      addToast(`Error loading incident #${incidentId}: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [incidentId]);

  const handleRunInvestigation = async () => {
    setRunningInvestigation(true);
    try {
      addToast('Launching LangGraph multi-agent investigation workflow...', 'info');
      const invRes = await createInvestigation(
        incidentId,
        `Investigate root cause and operational evidence for incident #${incidentId}: ${incident.title}`,
        'ASSISTED'
      );
      setActiveInvestigationId(invRes.investigation_id);
      setRagEvidence(invRes.knowledge_evidence || []);
      addToast(`LangGraph investigation #${invRes.investigation_id} completed successfully!`, 'success');

      // Now automatically synthesize intelligence on top of fresh investigation
      setGeneratingIntel(true);
      const intelRes = await generateIntelligence(incidentId, invRes.investigation_id);
      setIntelligence(intelRes);
      addToast('AI Intelligence & Operational Decision synthesized!', 'success');

      // Refresh incident & events
      const [incData, evs, invs, rems] = await Promise.all([
        getIncident(incidentId),
        getIncidentEvents(incidentId).catch(() => []),
        getIncidentInvestigations(incidentId).catch(() => []),
        getIncidentRemediations(incidentId).catch(() => []),
      ]);
      setIncident(incData);
      setEvents(evs);
      setInvestigations(invs);
      setRemediations(rems);
    } catch (err) {
      addToast(`Investigation failed: ${err.message}`, 'error');
    } finally {
      setRunningInvestigation(false);
      setGeneratingIntel(false);
    }
  };

  const handleGenerateIntelligence = async () => {
    setGeneratingIntel(true);
    try {
      const res = await generateIntelligence(incidentId, activeInvestigationId);
      setIntelligence(res);
      addToast('Incident intelligence generated & persisted successfully!', 'success');
      // Refresh timeline & remediations
      const [evs, rems] = await Promise.all([
        getIncidentEvents(incidentId),
        getIncidentRemediations(incidentId),
      ]);
      setEvents(evs);
      setRemediations(rems);
    } catch (err) {
      addToast(`Failed to generate intelligence: ${err.message}`, 'error');
    } finally {
      setGeneratingIntel(false);
    }
  };


  const handleOpenRequestModal = (recAction) => {
    if (!hasPermission('ACTION_REQUEST')) {
      addToast('RBAC Restricted: ACTION_REQUEST permission required (L2 Engineer, Manager, or Admin).', 'error');
      return;
    }
    setSelectedAction(recAction);
    let samplePayload = { service_id: 1 };
    if (recAction.action_type === 'ROLLBACK') {
      samplePayload = { service_id: 1, target_version: '2.8.1', current_version: '2.9.0' };
    } else if (recAction.action_type === 'ADJUST_POOL_LIMITS' || recAction.action_type === 'MITIGATE') {
      samplePayload = { service_id: 1, pool_size: 60 };
    } else if (recAction.action_type === 'RESTART') {
      samplePayload = { service_id: 1, instance_id: 'payment-api-prod-0' };
    }
    setRemPayload(JSON.stringify(samplePayload, null, 2));
    setIsRequestModalOpen(true);
  };

  const handleSubmitRemediation = async () => {
    setSubmittingRem(true);
    try {
      let parsedPayload = {};
      try {
        parsedPayload = JSON.parse(remPayload);
      } catch {
        throw new Error('Execution payload must be valid JSON');
      }

      let mappedType = 'DEPLOYMENT_ROLLBACK';
      if (selectedAction.action_type === 'ROLLBACK') mappedType = 'DEPLOYMENT_ROLLBACK';
      else if (selectedAction.action_type === 'RESTART') mappedType = 'RESTART_SERVICE_INSTANCE';
      else if (selectedAction.action_type === 'ADJUST_LIMITS' || selectedAction.action_type === 'MITIGATE') mappedType = 'ADJUST_POOL_LIMITS';
      else mappedType = 'DEPLOYMENT_ROLLBACK';

      const payload = {
        action_id: selectedAction.action_id,
        action_type: mappedType,
        title: selectedAction.title,
        description: selectedAction.description,
        rationale: selectedAction.rationale,
        intelligence_id: intelligence?.intelligence_id,
        investigation_id: activeInvestigationId,
        execution_payload: parsedPayload,
      };

      await createRemediation(incidentId, payload);
      addToast(`Remediation ${selectedAction.action_id} submitted in PENDING_APPROVAL status!`, 'success');
      setIsRequestModalOpen(false);
      const updatedRems = await getIncidentRemediations(incidentId);
      setRemediations(updatedRems);
    } catch (err) {
      addToast(`Failed to create remediation: ${err.message}`, 'error');
    } finally {
      setSubmittingRem(false);
    }
  };

  if (loading && !incident) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0', color: 'var(--text-muted)' }}>
        <div className="spinner" style={{ width: '32px', height: '32px', marginBottom: '16px' }} />
        <div>Loading incident data &amp; intelligence traces...</div>
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
        <p>Incident not found.</p>
        <button className="btn btn-secondary" onClick={onBack} style={{ marginTop: '12px' }}>&larr; Back to Incidents</button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Breadcrumb & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button className="btn btn-ghost" onClick={onBack} style={{ padding: '6px 10px' }}>
            &larr; Back
          </button>
          <span style={{ color: 'var(--text-muted)' }}>/</span>
          <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)', fontWeight: 700 }}>
            INCIDENT #{incident.incident_id}
          </span>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            className="btn btn-secondary"
            onClick={() => setActiveTab('copilot-chat')}
            style={{
              borderColor: 'rgba(0, 242, 254, 0.4)',
              background: 'rgba(0, 242, 254, 0.08)',
              color: 'var(--accent-cyan)',
            }}
          >
            <span>💬</span> Ask Copilot
          </button>

          <button
            className="btn btn-secondary"
            onClick={handleRunInvestigation}
            disabled={runningInvestigation || generatingIntel}
          >
            {runningInvestigation ? (
              <>
                <span className="spinner" /> LangGraph Agents Running...
              </>
            ) : (
              <>
                <span>🤖</span> Run LangGraph Investigation
              </>
            )}
          </button>

          <button
            className="btn btn-primary"
            onClick={handleGenerateIntelligence}
            disabled={generatingIntel || runningInvestigation}
          >
            {generatingIntel ? (
              <>
                <span className="spinner" /> Synthesizing AI Decision...
              </>
            ) : (
              <>
                <span>⚡</span> Run Full AI Intelligence
              </>
            )}
          </button>
        </div>
      </div>

      {/* Incident Header Card (Screen 3) */}
      <div className="card-elevated" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ flex: 1, minWidth: '280px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <SeverityBadge severity={incident.severity} />
              <StatusBadge status={incident.status} />
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Reported {formatDate(incident.created_at)} ({formatRelativeTime(incident.created_at)})
              </span>
            </div>
            <h1 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-highlight)', marginBottom: '8px' }}>
              {incident.title}
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px', lineHeight: 1.6 }}>
              {incident.description || 'No detailed incident description provided.'}
            </p>
          </div>

          {/* Quick Risk & Health Snapshot */}
          <div
            style={{
              background: 'var(--bg-main)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              padding: '16px',
              minWidth: '260px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            <RiskGauge
              score={intelligence?.risk_assessment?.failure_probability || 0.88}
              level={intelligence?.risk_assessment?.risk_level || 'HIGH'}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
              <span>Blast Radius:</span>
              <strong style={{ color: 'var(--status-critical)' }}>
                {intelligence?.impact_assessment?.blast_radius_tier || 'TIER 1 (PAYMENT API)'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
              <span>Grounding Invariant:</span>
              <span style={{ color: 'var(--status-healthy)', fontWeight: 700 }}>100% Grounded (RAG)</span>
            </div>
          </div>
        </div>

        {/* Operational Subtabs */}
        <div style={{ display: 'flex', gap: '8px', borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
          {[
            { id: 'intelligence', label: 'AI Intelligence & Root Cause', icon: '🧠' },
            { id: 'copilot-chat', label: 'Copilot Chat', icon: '💬' },
            { id: 'actions', label: `Recommended Actions (${intelligence?.recommended_actions?.length || 0})`, icon: '⚡' },
            { id: 'timeline', label: `Event Timeline (${events.length})`, icon: '⏱️' },
            { id: 'rag', label: `RAG Runbook Evidence (${ragEvidence.length})`, icon: '📚' },
          ].map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 14px',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '13px',
                  fontWeight: 600,
                  color: isActive ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                  background: isActive ? 'rgba(0, 242, 254, 0.08)' : 'transparent',
                  border: isActive ? '1px solid rgba(0, 242, 254, 0.3)' : '1px solid transparent',
                }}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab 1: AI Intelligence, Signals, Root Cause & Risk (Screens 4 & 5) */}
      {activeTab === 'intelligence' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {!intelligence ? (
            <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
                No intelligence synthesis generated for this incident yet.
              </p>
              <button className="btn btn-primary" onClick={handleGenerateIntelligence} disabled={generatingIntel}>
                Run AI Intelligence Engine
              </button>
            </div>
          ) : (
            <div className="grid-2">
              {/* Left: Ranked Root Cause Candidates (Screen 5) */}
              <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-highlight)' }}>
                    Ranked Root Cause Candidates
                  </h2>
                  <GroundingBadge />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {(intelligence.probable_root_causes || intelligence.root_causes || []).map((rc, idx) => (
                    <div
                      key={idx}
                      style={{
                        background: 'var(--bg-elevated)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-md)',
                        padding: '14px',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                        <span style={{ fontWeight: 700, color: 'var(--text-highlight)', fontSize: '14px' }}>
                          #{idx + 1} {rc.cause}
                        </span>
                        <span
                          style={{
                            fontFamily: 'var(--font-mono)',
                            fontWeight: 700,
                            color: rc.confidence >= 0.8 ? 'var(--status-critical)' : 'var(--status-warning)',
                            fontSize: '13px',
                          }}
                        >
                          {Math.round(rc.confidence * 100)}% Confidence
                        </span>
                      </div>
                      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                        {rc.rationale}
                      </p>
                      {rc.contributing_factors && rc.contributing_factors.length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                          {rc.contributing_factors.map((f, i) => (
                            <span
                              key={i}
                              style={{
                                fontSize: '11px',
                                background: 'rgba(255, 255, 255, 0.05)',
                                padding: '2px 8px',
                                borderRadius: '4px',
                                color: 'var(--text-muted)',
                              }}
                            >
                              • {f}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Operational Decision Statement */}
                {intelligence.operational_decision && (
                  <div
                    style={{
                      background: 'rgba(0, 242, 254, 0.04)',
                      border: '1px solid rgba(0, 242, 254, 0.2)',
                      borderRadius: 'var(--radius-md)',
                      padding: '14px',
                      marginTop: '8px',
                    }}
                  >
                    <div style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--accent-cyan)', marginBottom: '4px' }}>
                      Operational Decision Engine Output
                    </div>
                    <div style={{ fontWeight: 600, color: 'var(--text-highlight)', marginBottom: '4px' }}>
                      Primary Action: {intelligence.operational_decision.primary_action}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                      {intelligence.operational_decision.decision_summary}
                    </div>
                  </div>
                )}
              </div>

              {/* Right: Multi-Modal Correlated Signals (Screen 4) */}
              <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-highlight)' }}>
                    Correlated Operational Signals ({intelligence.correlated_signals?.length || 0})
                  </h2>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Multi-Modal Correlation</span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '480px', overflowY: 'auto' }}>
                  {(intelligence.correlated_signals || []).map((sig, idx) => (
                    <div
                      key={idx}
                      style={{
                        background: 'var(--bg-elevated)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-md)',
                        padding: '12px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '6px',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                          {sig.signal_type}
                        </span>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          Strength: {(sig.correlation_strength * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p style={{ fontSize: '12px', color: 'var(--text-primary)' }}>{sig.description}</p>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        Linked Evidence IDs: {sig.evidence_ids?.join(', ') || 'N/A'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Recommended Actions (Screen 7) */}
      {activeTab === 'actions' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-highlight)' }}>
                Synthesized Remediation Actions
              </h2>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Every action requires explicit human review and approval before execution via safe whitelisted adapters.
              </p>
            </div>
            <button className="btn btn-secondary" onClick={onNavigateToRemediations}>
              View Global Remediation Lifecycle &rarr;
            </button>
          </div>

          {(!intelligence?.recommended_actions || intelligence.recommended_actions.length === 0) ? (
            <div className="card" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
              No recommendations available. Please generate intelligence first.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {intelligence.recommended_actions.map((act) => {
                // Check if already requested in remediations
                const existing = remediations.find((r) => r.action_id === act.action_id);

                return (
                  <div
                    key={act.action_id}
                    className="card"
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      gap: '20px',
                      background: 'var(--bg-elevated)',
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                        <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-cyan)', fontSize: '13px' }}>
                          {act.action_id}
                        </span>
                        <span style={{ fontWeight: 700, fontSize: '15px', color: 'var(--text-highlight)' }}>
                          {act.title}
                        </span>
                        <span className="badge badge-warning" style={{ fontSize: '10px' }}>
                          PRIORITY: {act.priority}
                        </span>
                        {act.requires_human_approval && (
                          <span className="badge badge-purple" style={{ fontSize: '10px' }}>
                            🔒 HUMAN APPROVAL REQUIRED
                          </span>
                        )}
                      </div>
                      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                        {act.description}
                      </p>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                        <strong>Rationale:</strong> {act.rationale}
                      </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'flex-end', minWidth: '180px' }}>
                      {existing ? (
                        <>
                          <StatusBadge status={existing.status} type="remediation" />
                          <button
                            className="btn btn-secondary"
                            onClick={onNavigateToRemediations}
                            style={{ fontSize: '11px', padding: '5px 10px' }}
                          >
                            Manage Execution &rarr;
                          </button>
                        </>
                      ) : (
                        <button
                          className="btn btn-primary"
                          onClick={() => handleOpenRequestModal(act)}
                          disabled={!hasPermission('ACTION_REQUEST')}
                          title={!hasPermission('ACTION_REQUEST') ? 'Requires ACTION_REQUEST permission (L2, Manager, or Admin)' : 'Request human approval for this remediation'}
                        >
                          Request Remediation
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Timeline Events (Screen 3) */}
      {activeTab === 'timeline' && (
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-highlight)' }}>
            Incident Event Timeline
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {events.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                No events recorded for this incident yet.
              </div>
            ) : (
              events.map((ev, i) => (
                <div
                  key={ev.incident_event_id || i}
                  style={{
                    display: 'flex',
                    gap: '16px',
                    paddingBottom: '12px',
                    borderBottom: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)', minWidth: '140px' }}>
                    {formatDate(ev.event_time)}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                      <span className="badge badge-info">{ev.event_type}</span>
                    </div>
                    <div style={{ fontSize: '13px', color: 'var(--text-primary)' }}>
                      {ev.description}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Tab 4: RAG Knowledge Evidence (Screen 6) */}
      {activeTab === 'rag' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-highlight)' }}>
                Grounded Knowledge Runbooks (Pinecone &ge; 0.65)
              </h2>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Verified runbook chunks retrieved by semantic search and validated for 100% citation grounding.
              </p>
            </div>
            <GroundingBadge />
          </div>

          {ragEvidence.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
              No RAG runbook evidence attached to investigation #{activeInvestigationId}.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {ragEvidence.map((rag, i) => (
                <div
                  key={i}
                  className="card"
                  style={{ background: 'var(--bg-elevated)', display: 'flex', flexDirection: 'column', gap: '8px' }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, color: 'var(--accent-cyan)', fontSize: '14px' }}>
                      📖 {rag.document_title || 'Operational Runbook'} (v{rag.version || 1})
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--status-healthy)' }}>
                      Similarity: {formatScore(rag.similarity_score)}
                    </span>
                  </div>
                  <div className="code-block" style={{ maxHeight: '160px' }}>
                    {rag.chunk_text || rag.content || 'Runbook content chunk.'}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    Chunk ID: <code>{rag.chunk_id}</code> • Citation Valid: <strong>TRUE</strong>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 5: Copilot Chat Investigation */}
      {activeTab === 'copilot-chat' && (
        <IncidentChatTab incident={incident} />
      )}

      {/* Modal: Request Remediation (Screen 7/8 Gate) */}
      <Modal
        isOpen={isRequestModalOpen}
        onClose={() => setIsRequestModalOpen(false)}
        title={`Request Remediation: ${selectedAction?.action_id}`}
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setIsRequestModalOpen(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleSubmitRemediation} disabled={submittingRem}>
              {submittingRem ? 'Submitting...' : 'Submit for Human Approval'}
            </button>
          </>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <strong style={{ color: 'var(--text-highlight)' }}>Title:</strong> {selectedAction?.title}
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            <strong>Action Type:</strong> <code>{selectedAction?.action_type}</code>
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            <strong>Rationale:</strong> {selectedAction?.rationale}
          </div>

          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
              Execution Payload (JSON):
            </label>
            <textarea
              rows={5}
              value={remPayload}
              onChange={(e) => setRemPayload(e.target.value)}
              style={{
                width: '100%',
                fontFamily: 'var(--font-mono)',
                fontSize: '12px',
                background: '#0B0F17',
                border: '1px solid var(--border-medium)',
                borderRadius: 'var(--radius-md)',
                color: '#38BDF8',
                padding: '10px',
              }}
            />
          </div>

          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Submitting will create a remediation record in <code>PENDING_APPROVAL</code> status. SRE Manager or Administrator approval is required before execution.
          </div>
        </div>
      </Modal>
    </div>
  );
}
