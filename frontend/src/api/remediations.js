import { apiRequest } from './client';

export async function getIncidentRemediations(incidentId) {
  return apiRequest(`/api/v1/incidents/${incidentId}/remediations`);
}

export async function getRemediation(remediationId) {
  return apiRequest(`/api/v1/remediations/${remediationId}`);
}

export async function createRemediation(incidentId, payload) {
  return apiRequest(`/api/v1/incidents/${incidentId}/remediations`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function approveRemediation(remediationId, decision = 'APPROVE', reviewComment = '') {
  return apiRequest(`/api/v1/remediations/${remediationId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ decision, review_comment: reviewComment }),
  });
}

export async function rejectRemediation(remediationId, decision = 'REJECT', reviewComment = '') {
  return apiRequest(`/api/v1/remediations/${remediationId}/reject`, {
    method: 'POST',
    body: JSON.stringify({ decision, review_comment: reviewComment }),
  });
}

export async function executeRemediation(remediationId, dryRun = true) {
  return apiRequest(`/api/v1/remediations/${remediationId}/execute`, {
    method: 'POST',
    body: JSON.stringify({ dry_run: dryRun }),
  });
}

export async function verifyRemediation(remediationId, forceFail = false) {
  const query = forceFail ? '?force_fail=true' : '';
  return apiRequest(`/api/v1/remediations/${remediationId}/verify${query}`, {
    method: 'POST',
  });
}
