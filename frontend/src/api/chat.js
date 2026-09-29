import { apiRequest } from './client';

/**
 * Send a message to the conversational copilot.
 * 
 * @param {Object} payload
 * @param {string} payload.message - The user's query or prompt
 * @param {string|null} [payload.session_id] - Optional session ID to continue existing conversation
 * @param {number|null} [payload.incident_id] - Optional incident ID context
 * @returns {Promise<Object>} { session_id, answer, investigation_id, risk, citations, tool_trace }
 */
export async function sendChatMessage(payload) {
  return apiRequest('/api/v1/chat', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * List all chat sessions for the authenticated user.
 * 
 * @param {number} [limit=50]
 * @returns {Promise<Array<Object>>}
 */
export async function listChatSessions(limit = 50) {
  return apiRequest(`/api/v1/chat/sessions?limit=${limit}`);
}

/**
 * Retrieve the full message history of a specific chat session.
 * 
 * @param {string} sessionId
 * @returns {Promise<Object>}
 */
export async function getChatSession(sessionId) {
  return apiRequest(`/api/v1/chat/sessions/${encodeURIComponent(sessionId)}`);
}
