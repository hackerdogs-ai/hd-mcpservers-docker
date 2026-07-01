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

export function getHeygenKey() {
  return localStorage.getItem('hd_heygen_key') || '';
}

export function getHeygenAvatarId() {
  return localStorage.getItem('hd_heygen_avatar_id') || '';
}

export function getOpenAIKey() {
  return localStorage.getItem('hd_openai_key') || '';
}

export function getOllamaUrl() {
  return localStorage.getItem('hd_ollama_url') || '';
}

export function getBedrockApiKey() {
  return localStorage.getItem('hd_bedrock_api_key') || '';
}

export function getBedrockRegion() {
  return localStorage.getItem('hd_bedrock_region') || 'us-east-1';
}

export function getBedrockModels() {
  return localStorage.getItem('hd_bedrock_models') || '';
}

export function getAzureOpenAIKey() {
  return localStorage.getItem('hd_azure_openai_key') || '';
}

export function getAzureOpenAIEndpoint() {
  return localStorage.getItem('hd_azure_openai_endpoint') || '';
}

export function getAzureOpenAIModels() {
  return localStorage.getItem('hd_azure_openai_models') || '';
}

export function getOpenRouterKey() {
  return localStorage.getItem('hd_openrouter_key') || '';
}

export function getOpenRouterModels() {
  return localStorage.getItem('hd_openrouter_models') || '';
}

export function getGrokKey() {
  return localStorage.getItem('hd_grok_key') || '';
}

export function getGrokModels() {
  return localStorage.getItem('hd_grok_models') || '';
}

export function getGeminiKey() {
  return localStorage.getItem('hd_gemini_key') || '';
}

export function getGeminiModels() {
  return localStorage.getItem('hd_gemini_models') || '';
}

export function saveSettings({
  baseUrl,
  apiKey,
  adminSecret,
  claudeKey,
  openaiKey,
  ollamaUrl,
  heygenKey,
  heygenAvatarId,
  bedrockApiKey,
  bedrockRegion,
  bedrockModels,
  azureOpenaiKey,
  azureOpenaiEndpoint,
  azureOpenaiModels,
  openrouterKey,
  openrouterModels,
  grokKey,
  grokModels,
  geminiKey,
  geminiModels,
}) {
  if (baseUrl !== undefined) localStorage.setItem('hd_base_url', baseUrl);
  if (apiKey !== undefined) localStorage.setItem('hd_api_key', apiKey);
  if (adminSecret !== undefined) localStorage.setItem('hd_admin_secret', adminSecret);
  if (claudeKey !== undefined) localStorage.setItem('hd_claude_key', claudeKey);
  if (openaiKey !== undefined) localStorage.setItem('hd_openai_key', openaiKey);
  if (ollamaUrl !== undefined) localStorage.setItem('hd_ollama_url', ollamaUrl);
  if (heygenKey !== undefined) localStorage.setItem('hd_heygen_key', heygenKey);
  if (heygenAvatarId !== undefined) localStorage.setItem('hd_heygen_avatar_id', heygenAvatarId);
  if (bedrockApiKey !== undefined) localStorage.setItem('hd_bedrock_api_key', bedrockApiKey);
  if (bedrockRegion !== undefined) localStorage.setItem('hd_bedrock_region', bedrockRegion);
  if (bedrockModels !== undefined) localStorage.setItem('hd_bedrock_models', bedrockModels);
  if (azureOpenaiKey !== undefined) localStorage.setItem('hd_azure_openai_key', azureOpenaiKey);
  if (azureOpenaiEndpoint !== undefined) localStorage.setItem('hd_azure_openai_endpoint', azureOpenaiEndpoint);
  if (azureOpenaiModels !== undefined) localStorage.setItem('hd_azure_openai_models', azureOpenaiModels);
  if (openrouterKey !== undefined) localStorage.setItem('hd_openrouter_key', openrouterKey);
  if (openrouterModels !== undefined) localStorage.setItem('hd_openrouter_models', openrouterModels);
  if (grokKey !== undefined) localStorage.setItem('hd_grok_key', grokKey);
  if (grokModels !== undefined) localStorage.setItem('hd_grok_models', grokModels);
  if (geminiKey !== undefined) localStorage.setItem('hd_gemini_key', geminiKey);
  if (geminiModels !== undefined) localStorage.setItem('hd_gemini_models', geminiModels);
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

/** Fetch README markdown for a server */
export async function getServerReadme(name) {
  const url = `${getBaseUrl()}/services/${encodeURIComponent(name)}/readme`;
  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.text();
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

/** Enable a server (add to Caddy routing) */
export async function enableServer(name) {
  return apiFetch(`/admin/servers/${name}/enable`, {
    method: 'POST',
    headers: adminHeaders(),
  });
}

/** Disable a server (remove from Caddy routing) */
export async function disableServer(name) {
  return apiFetch(`/admin/servers/${name}/disable`, {
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

/** Create a new MCP server (Docker image or external HTTP endpoint) */
export async function createServer(payload) {
  return apiFetch('/admin/servers', {
    method: 'POST',
    headers: adminHeaders(),
    body: JSON.stringify(payload),
  });
}

/** Delete an MCP server */
export async function deleteServer(name) {
  return apiFetch(`/admin/servers/${encodeURIComponent(name)}`, {
    method: 'DELETE',
    headers: adminHeaders(),
  });
}

/** Import servers from Claude/Cursor JSON config */
export async function importServers(mcpServers) {
  return apiFetch('/admin/servers/import', {
    method: 'POST',
    headers: adminHeaders(),
    body: JSON.stringify({ mcpServers }),
  });
}
