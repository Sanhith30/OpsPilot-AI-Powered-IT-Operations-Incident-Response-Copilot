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

export function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [selectedIncidentId, setSelectedIncidentId] = useState(1);

  const handleSelectIncident = (id) => {
    setSelectedIncidentId(id);
    setActiveTab('incident-detail');
  };

  return (
    <AuthProvider>
      <ToastProvider>
        <MainLayout activeTab={activeTab === 'incident-detail' ? 'incidents' : activeTab} onSelectTab={setActiveTab}>
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
