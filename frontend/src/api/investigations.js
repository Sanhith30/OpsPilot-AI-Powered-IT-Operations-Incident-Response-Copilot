import { apiRequest } from './client';

export async function getInvestigation(investigationId) {
  return apiRequest(`/api/v1/investigations/${investigationId}`);
}

export async function getInvestigationDetails(investigationId) {
  return apiRequest(`/api/v1/investigations/${investigationId}/details`);
}

export async function getRagEvidence(investigationId) {
  return apiRequest(`/api/v1/investigations/${investigationId}/rag-evidence`);
}

export async function getInvestigationAudit(investigationId) {
  return apiRequest(`/api/v1/investigations/${investigationId}/audit`);
}

export async function createInvestigation(incidentId, question = 'Investigate incident root causes and operational evidence', investigationType = 'ASSISTED') {
  return apiRequest('/api/v1/investigations', {
    method: 'POST',
    body: JSON.stringify({
      incident_id: incidentId,
      question,
      investigation_type: investigationType,
    }),
  });
}
