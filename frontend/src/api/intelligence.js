import { apiRequest } from './client';

export async function getIntelligence(incidentId) {
  return apiRequest(`/api/v1/incidents/${incidentId}/intelligence`);
}

export async function generateIntelligence(incidentId, investigationId = null) {
  const query = investigationId ? `?investigation_id=${investigationId}` : '';
  return apiRequest(`/api/v1/incidents/${incidentId}/intelligence${query}`, {
    method: 'POST',
  });
}
