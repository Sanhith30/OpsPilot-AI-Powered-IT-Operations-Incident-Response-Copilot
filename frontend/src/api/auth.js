import { apiRequest } from './client';

export async function login(email, password) {
  return apiRequest('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function getMe() {
  return apiRequest('/api/v1/auth/me');
}
