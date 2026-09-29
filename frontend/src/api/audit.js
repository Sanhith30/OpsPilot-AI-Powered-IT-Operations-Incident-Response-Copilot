import { apiRequest } from './client';

export async function getAuditLogs(limit = 50, resourceType = null) {
  const query = resourceType ? `?limit=${limit}&resource_type=${resourceType}` : `?limit=${limit}`;
  return apiRequest(`/api/v1/audit-logs${query}`);
}
