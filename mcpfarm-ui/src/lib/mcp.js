// mcp.js — MCP session lifecycle management
//
// Session recovery follows MCP Streamable HTTP spec (2025-03-26 §Session Management):
// https://modelcontextprotocol.io/specification/2025-03-26/basic/transports#session-management
// On HTTP 404 with Mcp-Session-Id, clients MUST re-initialize (see also TS SDK #1708).

import { getBaseUrl, getApiKey } from './api.js';

function parseSseResponse(text) {
  for (const line of text.split('\n')) {
    if (line.startsWith('data: ')) {
      try {
        return JSON.parse(line.slice(6));
      } catch {
        // keep trying other lines
      }
    }
  }
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

export class McpClient {
  constructor() {
    // Map of serverName -> sessionId
    this.sessions = {};
    // Map of serverName -> request id counter
    this.idCounters = {};
  }

  _nextId(serverName) {
    if (!this.idCounters[serverName]) this.idCounters[serverName] = 1;
    return this.idCounters[serverName]++;
  }

  _headers(sessionId) {
    const key = getApiKey();
    const h = {
      'Content-Type': 'application/json',
      Accept: 'application/json, text/event-stream',
    };
    if (key) h['Authorization'] = `Bearer ${key}`;
    if (sessionId) h['mcp-session-id'] = sessionId;
    return h;
  }

  _endpoint(serverName) {
    return `${getBaseUrl()}/${serverName}/mcp`;
  }

  async _post(serverName, body, sessionId, { retryOn404 = true } = {}) {
    const url = this._endpoint(serverName);
    const res = await fetch(url, {
      method: 'POST',
      headers: this._headers(sessionId),
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      // Spec: 404 + session ID => session terminated; clear and re-init once.
      if (retryOn404 && res.status === 404 && sessionId) {
        this.resetSession(serverName);
        await this.initialize(serverName);
        return this._post(serverName, body, this.sessions[serverName], { retryOn404: false });
      }

      // Upstream unreachable — drop cached session so the next start is clean.
      if (res.status === 502 || res.status === 503) {
        this.resetSession(serverName);
      }

      const text = await res.text().catch(() => res.statusText);
      const hint = res.status === 502 || res.status === 503
        ? ' (MCP server unreachable — is the container running?)'
        : res.status === 401
          ? ' (check API key in Settings)'
          : res.status === 404
            ? ' (session expired — retry or refresh the page)'
            : res.status === 400
              ? ' (bad request — session may be stale; retry or refresh)'
              : '';
      throw new Error(`MCP HTTP ${res.status}${hint}: ${text}`.trim());
    }

    // Capture session ID from response header
    const newSession = res.headers.get('mcp-session-id');
    if (newSession) {
      this.sessions[serverName] = newSession;
    }

    const text = await res.text();
    return parseSseResponse(text);
  }

  /** Initialize an MCP session for a server */
  async initialize(serverName) {
    const initBody = {
      jsonrpc: '2.0',
      id: this._nextId(serverName),
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: { tools: {} },
        clientInfo: { name: 'mcpfarm-ui', version: '1.0.0' },
      },
    };

    const initResult = await this._post(serverName, initBody, null, { retryOn404: false });

    // Send initialized notification
    const notifyBody = {
      jsonrpc: '2.0',
      method: 'notifications/initialized',
      params: {},
    };
    const sessionId = this.sessions[serverName];
    await fetch(this._endpoint(serverName), {
      method: 'POST',
      headers: this._headers(sessionId),
      body: JSON.stringify(notifyBody),
    }).catch(() => {});

    return initResult;
  }

  /** Spec SHOULD: terminate session via DELETE before disconnecting. */
  async terminateSession(serverName) {
    const sessionId = this.sessions[serverName];
    if (!sessionId) return;
    try {
      await fetch(this._endpoint(serverName), {
        method: 'DELETE',
        headers: this._headers(sessionId),
      });
    } catch {
      // Server may already be stopped (ECONNREFUSED / 502 via proxy).
    } finally {
      this.resetSession(serverName);
    }
  }

  /** List tools for a server. Auto-initializes if no session. */
  async listTools(serverName) {
    if (!this.sessions[serverName]) {
      await this.initialize(serverName);
    }

    const body = {
      jsonrpc: '2.0',
      id: this._nextId(serverName),
      method: 'tools/list',
      params: {},
    };

    const result = await this._post(serverName, body, this.sessions[serverName]);

    if (result && result.error) {
      throw new Error(result.error.message || JSON.stringify(result.error));
    }

    if (result && result.result) {
      return result.result.tools || [];
    }
    if (result && Array.isArray(result.tools)) {
      return result.tools;
    }
    if (Array.isArray(result)) {
      return result;
    }
    return [];
  }

  /** Call a tool on a server */
  async callTool(serverName, toolName, args) {
    if (!this.sessions[serverName]) {
      await this.initialize(serverName);
    }

    const body = {
      jsonrpc: '2.0',
      id: this._nextId(serverName),
      method: 'tools/call',
      params: {
        name: toolName,
        arguments: args || {},
      },
    };

    const result = await this._post(serverName, body, this.sessions[serverName]);

    if (result && result.error) {
      throw new Error(result.error.message || JSON.stringify(result.error));
    }

    if (result && result.result !== undefined) {
      return result.result;
    }

    return result;
  }

  /** Reset/clear session for a server */
  resetSession(serverName) {
    delete this.sessions[serverName];
    delete this.idCounters[serverName];
  }

  /** Reset all sessions */
  resetAll() {
    this.sessions = {};
    this.idCounters = {};
  }
}

// Singleton instance shared across the app
export const mcpClient = new McpClient();
