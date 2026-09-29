import React, { useState } from 'react';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { MainLayout } from './layouts/MainLayout';
import { DashboardPage } from './pages/DashboardPage';
import { IncidentsPage } from './pages/IncidentsPage';
import { IncidentDetailPage } from './pages/IncidentDetailPage';
import { RemediationsPage } from './pages/RemediationsPage';
import { KnowledgePage } from './pages/KnowledgePage';
import { AuditPage } from './pages/AuditPage';
import { ChatPage } from './pages/ChatPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { useEffect } from 'react';

export function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [selectedIncidentId, setSelectedIncidentId] = useState(1);

  // Update dynamic page title on tab changes
  useEffect(() => {
    const titles = {
      chat: 'Ask Copilot - Multi-Tool Investigation | OpsPilot',
      dashboard: 'Operations Dashboard & Fleet KPIs | OpsPilot',
      incidents: 'Incidents & Operational Triage | OpsPilot',
      'incident-detail': `Incident #${selectedIncidentId} Root Cause & Timeline | OpsPilot`,
      remediations: 'Remediation Actions & Human Approval Portal | OpsPilot',
      knowledge: 'Operational Runbooks & RAG Knowledge Base | OpsPilot',
      audit: 'Immutable Audit Trail & OpenTelemetry | OpsPilot',
    };
    document.title = titles[activeTab] || 'OpsPilot - Enterprise SRE Copilot';
  }, [activeTab, selectedIncidentId]);

  const handleSelectIncident = (id) => {
    setSelectedIncidentId(id);
    setActiveTab('incident-detail');
  };

  const validTabs = ['chat', 'dashboard', 'incidents', 'incident-detail', 'remediations', 'knowledge', 'audit'];
  const isNotFound = !validTabs.includes(activeTab);

  return (
    <AuthProvider>
      <ToastProvider>
        <MainLayout activeTab={activeTab === 'incident-detail' ? 'incidents' : activeTab} onSelectTab={setActiveTab}>
          {isNotFound && (
            <NotFoundPage onNavigateHome={() => setActiveTab('dashboard')} />
          )}

          {activeTab === 'chat' && (
            <ChatPage
              defaultIncidentId={null}
              onNavigateToIncident={handleSelectIncident}
            />
          )}

          {activeTab === 'dashboard' && (
            <DashboardPage
              onNavigateToIncident={handleSelectIncident}
              onNavigateToTab={setActiveTab}
            />
          )}

          {activeTab === 'incidents' && (
            <IncidentsPage onSelectIncident={handleSelectIncident} />
          )}

          {activeTab === 'incident-detail' && (
            <IncidentDetailPage
              incidentId={selectedIncidentId}
              onBack={() => setActiveTab('incidents')}
              onNavigateToRemediations={() => setActiveTab('remediations')}
            />
          )}

          {activeTab === 'remediations' && (
            <RemediationsPage
              onNavigateToIncident={handleSelectIncident}
            />
          )}

          {activeTab === 'knowledge' && (
            <KnowledgePage />
          )}

          {activeTab === 'audit' && (
            <AuditPage />
          )}
        </MainLayout>
      </ToastProvider>
    </AuthProvider>
  );
}

export default App;
