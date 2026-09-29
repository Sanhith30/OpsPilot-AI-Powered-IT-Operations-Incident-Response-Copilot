import React, { useEffect, useState } from 'react';
import { getKnowledgeDocuments, searchKnowledge } from '../api/knowledge';
import { GroundingBadge } from '../components/GroundingBadge';
import { useToast } from '../context/ToastContext';
import { formatDate, formatScore } from '../utils/formatters';

export function KnowledgePage() {
  const { addToast } = useToast();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const docs = await getKnowledgeDocuments();
      setDocuments(docs);
    } catch (err) {
      addToast(`Error loading knowledge base: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearching(true);
    try {
      const res = await searchKnowledge(searchQuery);
      setSearchResults(res);
      addToast(`Retrieved ${res?.chunks?.length || 0} matching runbook chunks`, 'info');
    } catch (err) {
      addToast(`Search failed: ${err.message}`, 'error');
    } finally {
      setSearching(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <span>Knowledge Base &amp; Grounded RAG</span>
          </h1>
          <p className="page-subtitle">
            Curated operational runbooks, SOPs, and postmortems indexed in Pinecone with strict 0.65 threshold &amp; 100% citation grounding.
          </p>
        </div>
        <GroundingBadge />
      </div>

      {/* Semantic Search Box */}
      <div className="card-elevated">
        <h2 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-highlight)', marginBottom: '8px' }}>
          Semantic Runbook Retrieval &amp; Grounding Probe
        </h2>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
          Queries are embedded via Gemini, filtered through candidate K=15, and reranked to top K=5 with similarity gate &ge; 0.65.
        </p>

        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            placeholder="e.g. database connection pool exhaustion payment api..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              flex: 1,
              background: 'var(--bg-main)',
              border: '1px solid var(--border-medium)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 16px',
              fontSize: '13px',
              color: 'var(--text-primary)',
            }}
          />
          <button className="btn btn-primary" type="submit" disabled={searching}>
            {searching ? <><span className="spinner" /> Searching...</> : 'Semantic Search'}
          </button>
        </form>

        {/* Search Results Display */}
        {searchResults && (
          <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-highlight)' }}>
                Top Ranked Chunks ({searchResults.chunks?.length || 0})
              </span>
              <button className="btn btn-ghost" onClick={() => setSearchResults(null)} style={{ fontSize: '11px' }}>
                Clear Results
              </button>
            </div>

            {searchResults.chunks?.length === 0 ? (
              <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)' }}>
                No chunks surpassed the 0.65 similarity safety gate (Clean Rejection).
              </div>
            ) : (
              searchResults.chunks?.map((chunk, i) => (
                <div
                  key={i}
                  style={{
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '14px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>
                      #{i + 1} {chunk.document_title || chunk.title} (v{chunk.version || 1})
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--status-healthy)', fontWeight: 700 }}>
                      Score: {formatScore(chunk.score || chunk.similarity_score)}
                    </span>
                  </div>
                  <div className="code-block" style={{ maxHeight: '120px' }}>
                    {chunk.text || chunk.content}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Indexed Documents Table */}
      <div className="card">
        <h2 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-highlight)', marginBottom: '16px' }}>
          Indexed Operational Documents ({documents.length})
        </h2>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>
            <div className="spinner" style={{ marginBottom: '12px' }} />
            <div>Loading documents...</div>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Doc ID</th>
                  <th>Title</th>
                  <th>Type</th>
                  <th>Current Version</th>
                  <th>Team</th>
                  <th>Updated</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.document_id}>
                    <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                      {doc.document_id}
                    </td>
                    <td style={{ fontWeight: 600, color: 'var(--text-highlight)' }}>
                      {doc.title}
                    </td>
                    <td>
                      <span className="badge badge-info">{doc.document_type || 'RUNBOOK'}</span>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>
                      v{doc.current_version_id || 1}
                    </td>
                    <td>{doc.owner_team_id ? `Team #${doc.owner_team_id}` : 'Platform SRE'}</td>
                    <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      {formatDate(doc.updated_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
