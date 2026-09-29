import React, { useState } from 'react';

const TOOL_ICONS = {
  search_logs: '📋',
  query_metrics: '📈',
  query_database_readonly: '🗄️',
  retrieve_runbook_context: '📚',
  predict_incident_risk: '🧠',
  list_recent_incidents: '🚨',
  get_incident_details: '🔍',
  get_service_deployments: '🚀',
  create_ticket: '🎫',
  update_ticket: '📝',
  default: '⚡',
};

const TOOL_CATEGORIES = {
  search_logs: 'LOGS',
  query_metrics: 'METRICS',
  query_database_readonly: 'SQL',
  retrieve_runbook_context: 'RAG RUNBOOKS',
  predict_incident_risk: 'ML RISK',
  list_recent_incidents: 'INCIDENTS',
  get_incident_details: 'INCIDENTS',
  get_service_deployments: 'DEPLOYMENTS',
  create_ticket: 'TICKETING',
  update_ticket: 'TICKETING',
  default: 'TOOL',
};

export function ToolTraceExpander({ toolTrace }) {
  const [isOpen, setIsOpen] = useState(false);
  const [expandedIndex, setExpandedIndex] = useState(null);

  if (!toolTrace || toolTrace.length === 0) return null;

  return (
    <div
      style={{
        margin: '10px 0',
        borderRadius: 'var(--radius-md)',
        background: 'rgba(8, 12, 20, 0.6)',
        border: '1px solid var(--border-subtle)',
        overflow: 'hidden',
        fontSize: '12px',
      }}
    >
      {/* Header bar */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '100%',
          padding: '8px 12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: isOpen ? 'rgba(0, 242, 254, 0.05)' : 'transparent',
          borderBottom: isOpen ? '1px solid var(--border-subtle)' : 'none',
          color: 'var(--text-secondary)',
          cursor: 'pointer',
          textAlign: 'left',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '13px' }}>🛠️</span>
          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
            Investigation Tool Trace
          </span>
          <span
            style={{
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              background: 'rgba(0, 242, 254, 0.12)',
              color: 'var(--accent-cyan)',
              padding: '1px 6px',
              borderRadius: '4px',
              border: '1px solid rgba(0, 242, 254, 0.25)',
            }}
          >
            {toolTrace.length} {toolTrace.length === 1 ? 'tool called' : 'tools called'}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            {isOpen ? 'Collapse' : 'Inspect'}
          </span>
          <span style={{ transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}>
            ▼
          </span>
        </div>
      </button>

      {/* Expanded Tools List */}
      {isOpen && (
        <div style={{ padding: '8px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {toolTrace.map((tool, idx) => {
            const isSingleExpanded = expandedIndex === idx;
            const icon = TOOL_ICONS[tool.tool_name] || TOOL_ICONS.default;
            const cat = TOOL_CATEGORIES[tool.tool_name] || TOOL_CATEGORIES.default;
            const isSuccess = tool.status !== 'ERROR' && tool.status !== 'FAILED';

            return (
              <div
                key={idx}
                style={{
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--bg-main)',
                  border: '1px solid var(--border-subtle)',
                  padding: '8px 10px',
                }}
              >
                <div
                  onClick={() => setExpandedIndex(isSingleExpanded ? null : idx)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    userSelect: 'none',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span>{icon}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--accent-cyan)' }}>
                      {tool.tool_name}
                    </span>
                    <span
                      style={{
                        fontSize: '9px',
                        background: 'rgba(255, 255, 255, 0.06)',
                        color: 'var(--text-muted)',
                        padding: '1px 5px',
                        borderRadius: '3px',
                      }}
                    >
                      {cat}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span
                      style={{
                        fontSize: '10px',
                        fontFamily: 'var(--font-mono)',
                        color: isSuccess ? 'var(--status-healthy)' : 'var(--status-critical)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                    >
                      <span>{isSuccess ? '●' : '✕'}</span>
                      {tool.status || 'SUCCESS'}
                    </span>
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                      {isSingleExpanded ? '▲' : '▼'}
                    </span>
                  </div>
                </div>

                {/* Summary snippet */}
                {tool.result_summary && !isSingleExpanded && (
                  <div
                    style={{
                      fontSize: '11px',
                      color: 'var(--text-muted)',
                      marginTop: '4px',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {tool.result_summary}
                  </div>
                )}

                {/* Detailed inspector */}
                {isSingleExpanded && (
                  <div
                    style={{
                      marginTop: '8px',
                      paddingTop: '8px',
                      borderTop: '1px dashed var(--border-subtle)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '6px',
                    }}
                  >
                    {tool.parameters && Object.keys(tool.parameters).length > 0 && (
                      <div>
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '3px' }}>
                          PARAMETERS:
                        </div>
                        <pre
                          style={{
                            background: '#0B0F17',
                            padding: '6px 8px',
                            borderRadius: '4px',
                            fontSize: '11px',
                            fontFamily: 'var(--font-mono)',
                            color: '#38BDF8',
                            overflowX: 'auto',
                            margin: 0,
                          }}
                        >
                          {JSON.stringify(tool.parameters, null, 2)}
                        </pre>
                      </div>
                    )}

                    {tool.result_summary && (
                      <div>
                        <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '3px' }}>
                          RESULT:
                        </div>
                        <div
                          style={{
                            background: '#0B0F17',
                            padding: '6px 8px',
                            borderRadius: '4px',
                            fontSize: '11px',
                            fontFamily: 'var(--font-mono)',
                            color: 'var(--text-secondary)',
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word',
                            maxHeight: '180px',
                            overflowY: 'auto',
                          }}
                        >
                          {tool.result_summary}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
