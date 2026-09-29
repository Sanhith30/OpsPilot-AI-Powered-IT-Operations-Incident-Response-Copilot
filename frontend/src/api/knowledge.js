import { apiRequest } from './client';

export async function getKnowledgeDocuments() {
  return apiRequest('/api/v1/knowledge/documents');
}

export async function getKnowledgeDocument(documentId) {
  return apiRequest(`/api/v1/knowledge/documents/${documentId}`);
}

export async function searchKnowledge(query, filters = {}) {
  return apiRequest('/api/v1/knowledge/search', {
    method: 'POST',
    body: JSON.stringify({ query, ...filters }),
  });
}
