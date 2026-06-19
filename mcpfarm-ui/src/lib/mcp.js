// mcp.js — MCP session lifecycle management

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

  async _post(serverName, body, sessionId) {
    const url = `${getBaseUrl()}/${serverName}/mcp`;
    const res = await fetch(url, {
      method: 'POST',
      headers: this._headers(sessionId),
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText);
      throw new Error(`MCP HTTP ${res.status}: ${text}`);
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

    const initResult = await this._post(serverName, initBody, null);

    // Send initialized notification
    const notifyBody = {
      jsonrpc: '2.0',
      method: 'notifications/initialized',
      params: {},
    };
    // Notification: no id, response may be empty
    const sessionId = this.sessions[serverName];
    await fetch(`${getBaseUrl()}/${serverName}/mcp`, {
      method: 'POST',
      headers: this._headers(sessionId),
      body: JSON.stringify(notifyBody),
    }).catch(() => {});

    return initResult;
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

    // Handle both JSON-RPC result wrapper and direct tools array
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
