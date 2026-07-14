/**
 * Thin wrapper around fetch that attaches auth headers automatically.
 * All ERP pages should import `apiFetch` instead of calling fetch directly.
 */

function getHeaders() {
  if (typeof window === 'undefined') return {};
  const token = localStorage.getItem('access_token');
  const tenantId = localStorage.getItem('tenant_id');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (tenantId) headers['X-Tenant-ID'] = tenantId;
  return headers;
}

const BASE = typeof process !== 'undefined' && process.env.NEXT_PUBLIC_API_URL
  ? process.env.NEXT_PUBLIC_API_URL
  : '';

export async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { ...getHeaders(), ...(options.headers || {}) },
  });

  if (res.status === 401) {
    if (typeof window !== 'undefined') {
      localStorage.clear();
      window.location.href = '/login';
    }
    throw new Error('Unauthorized');
  }

  if (!res.ok) {
    let errorBody;
    try { errorBody = await res.json(); } catch (_) { errorBody = {}; }
    const msg = errorBody?.detail || errorBody?.error || `HTTP ${res.status}`;
    throw new Error(msg);
  }

  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

export const api = {
  get: (path) => apiFetch(path),
  post: (path, body) => apiFetch(path, { method: 'POST', body: JSON.stringify(body) }),
  put: (path, body) => apiFetch(path, { method: 'PUT', body: JSON.stringify(body) }),
  patch: (path, body) => apiFetch(path, { method: 'PATCH', body: JSON.stringify(body) }),
  del: (path) => apiFetch(path, { method: 'DELETE' }),
};
