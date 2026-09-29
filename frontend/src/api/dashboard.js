import { apiRequest } from './client';

export async function getDashboardSummary() {
  return apiRequest('/api/v1/dashboard/summary');
}
