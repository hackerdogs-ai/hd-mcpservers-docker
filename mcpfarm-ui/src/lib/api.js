// api.js — REST gateway calls for Hackerdogs MCP Farm

const DEFAULT_BASE_URL = ''; // empty = relative URLs (Vite proxy in dev, same-origin in prod)

export function getBaseUrl() {
  return localStorage.getItem('hd_base_url') || DEFAULT_BASE_URL;
}

export function getApiKey() {
  return localStorage.getItem('hd_api_key') || '';
}

export function getAdminSecret() {
  return localStorage.getItem('hd_admin_secret') || '';
}

export function getClaudeKey() {
  return localStorage.getItem('hd_claude_key') || '';
}

export function saveSettings({ baseUrl, apiKey, adminSecret, claudeKey }) {
  if (baseUrl !== undefined) localStorage.setItem('hd_base_url', baseUrl);
  if (apiKey !== undefined) localStorage.setItem('hd_api_key', apiKey);
  if (adminSecret !== undefined) localStorage.setItem('hd_admin_secret', adminSecret);
  if (claudeKey !== undefined) localStorage.setItem('hd_claude_key', claudeKey);
}

function authHeaders(extra = {}) {
  const key = getApiKey();
  return {
    'Content-Type': 'application/json',
    ...(key ? { Authorization: `Bearer ${key}` } : {}),
    ...extra,
  };
}

function adminHeaders() {
  const secret = getAdminSecret();
  return {
    ...authHeaders(),
    ...(secret ? { 'X-Admin-Secret': secret } : {}),
  };
}

async function apiFetch(path, options = {}) {
  const url = `${getBaseUrl()}${path}`;
  const res = await fetch(url, options);
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) {
    return res.json();
  }
  return res.text();
}

/** List all servers with status */
export async function listServices() {
  return apiFetch('/services', { headers: authHeaders() });
}

/** Get admin stats */
export async function getAdminStats() {
  return apiFetch('/admin/stats', { headers: adminHeaders() });
}

/** List API keys */
export async function listApiKeys() {
  return apiFetch('/admin/keys', { headers: adminHeaders() });
}

/** Create API key */
export async function createApiKey(label) {
  return apiFetch('/admin/keys', {
    method: 'POST',
    headers: adminHeaders(),
    body: JSON.stringify({ label }),
  });
}

/** Revoke API key */
export async function revokeApiKey(id) {
  return apiFetch(`/admin/keys/${id}`, {
    method: 'DELETE',
    headers: adminHeaders(),
  });
}

/** Start a server container */
export async function startServer(name) {
  return apiFetch(`/admin/servers/${name}/start`, {
    method: 'POST',
    headers: adminHeaders(),
  });
}

/** Stop a server container */
export async function stopServer(name) {
  return apiFetch(`/admin/servers/${name}/stop`, {
    method: 'POST',
    headers: adminHeaders(),
  });
}

/** Update env vars for a server */
export async function updateServerEnv(name, env) {
  return apiFetch(`/admin/servers/${name}/env`, {
    method: 'PATCH',
    headers: adminHeaders(),
    body: JSON.stringify(env),
  });
}

/** Reload Caddy routes */
export async function reloadRoutes() {
  return apiFetch('/admin/reload', {
    method: 'POST',
    headers: adminHeaders(),
  });
}

/** Rotate admin secret — returns { admin_secret, api_key } */
export async function rotateSecret() {
  return apiFetch('/admin/rotate-secret', {
    method: 'POST',
    headers: adminHeaders(),
  });
}
