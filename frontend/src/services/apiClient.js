import { API_BASE_URL } from '../config';

// In-memory token. Set by the auth layer on login and restored from
// AsyncStorage on app start. Injected into every request below.
let authToken = null;

export function setAuthToken(token) {
  authToken = token;
}

export function getAuthToken() {
  return authToken;
}

// Core request helper. Handles JSON encoding, auth header injection, and
// turning non-2xx responses into thrown Errors with the server's message.
export async function apiRequest(path, { method = 'GET', body, headers = {}, isForm = false } = {}) {
  const finalHeaders = { ...headers };

  if (authToken) {
    finalHeaders['Authorization'] = `Bearer ${authToken}`;
  }

  let finalBody = body;
  if (body && !isForm) {
    finalHeaders['Content-Type'] = 'application/json';
    finalBody = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: finalHeaders,
      body: finalBody,
    });
  } catch (err) {
    // Network-level failure (server down, wrong IP, no Wi-Fi, etc.)
    throw new Error('Could not reach the server. Check your connection and API_BASE_URL.');
  }

  let data = null;
  const text = await response.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!response.ok) {
    const detail = data && data.detail ? data.detail : `Request failed (${response.status})`;
    throw new Error(typeof detail === 'string' ? detail : 'Request failed');
  }

  return data;
}
