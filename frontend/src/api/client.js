/**
 * OpsPilot API Client
 * Centralized fetch client that automatically attaches the active JWT Bearer token
 * and handles consistent error responses.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem('opspilot_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Parse JSON if response has content
    const text = await response.text();
    let data = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        data = { raw: text };
      }
    }

    if (!response.ok) {
      const errorMsg = data?.detail || data?.error || response.statusText || 'Request failed';
      const error = new Error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  } catch (err) {
    console.error(`API Error on [${options.method || 'GET'}] ${endpoint}:`, err);
    throw err;
  }
}
