import { apiRequest } from './client';

export async function getIncidents() {
  return apiRequest('/api/v1/incidents');
}

export async function getIncident(incidentId) {
  return apiRequest(`/api/v1/incidents/${incidentId}`);
}

export async function getIncidentEvents(incidentId) {
  return apiRequest(`/api/v1/incidents/${incidentId}/events`);
}

export async function getIncidentInvestigations(incidentId) {
  return apiRequest(`/api/v1/incidents/${incidentId}/investigations`);
}
