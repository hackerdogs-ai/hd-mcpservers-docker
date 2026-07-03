/**
 * Tool binding helpers shared by the Chat page and per-server Chat tab.
 *
 * A "binding" is the concrete set of MCP tools exposed to the LLM for a turn,
 * plus the servers they belong to. Two strategies produce bindings:
 *
 *   - static:  the caller already knows the servers/tools (per-server tab, or
 *              the user's manual selection on the Chat page).
 *   - dynamic: vector search picks servers/tools from the user's query.
 */
import { mcpClient } from './mcp.js';
import { vectorSearch } from './api.js';

/** Resolve a promise but give up after `ms` so one dead server can't hang a turn. */
function withTimeout(promise, ms) {
  return Promise.race([
    promise,
    new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), ms)),
  ]);
}

/**
 * A bound tool carries enough metadata to (a) present to the LLM and (b) route
 * execution back to the owning server.
 * @typedef {{ server: string, name: string, description?: string, inputSchema?: object, score?: number }} BoundTool
 * @typedef {{ servers: string[], tools: BoundTool[], mode: 'static'|'dynamic', notes?: string }} Binding
 */

/** Build a static binding from an explicit server + tool list. */
export function toStaticBinding(server, tools = []) {
  const bound = (tools || [])
    .filter((t) => t && t.name)
    .map((t) => ({
      server,
      name: t.name,
      description: t.description || '',
      inputSchema: t.inputSchema || t.input_schema || { type: 'object', properties: {} },
    }));
  return { servers: bound.length ? [server] : [], tools: bound, mode: 'static' };
}

/** Merge several static per-server tool lists into one binding. */
export function mergeStaticBindings(perServer = []) {
  const tools = [];
  const servers = [];
  for (const { server, tools: list } of perServer) {
    if (!server) continue;
    const b = toStaticBinding(server, list);
    if (b.tools.length) {
      servers.push(server);
      tools.push(...b.tools);
    }
  }
  return { servers, tools, mode: 'static' };
}

/**
 * Resolve a static binding for a manual selection.
 * `selection` = { servers: string[], tools: { [server]: toolName[] } }
 * Tool schemas are fetched live from each running server.
 */
export async function resolveStaticSelection(selection) {
  const { servers = [], tools = {} } = selection || {};
  const perServer = [];
  for (const server of servers) {
    let live = [];
    try {
      live = await mcpClient.listTools(server);
    } catch {
      live = [];
    }
    const wanted = tools[server];
    const filtered = wanted && wanted.length
      ? live.filter((t) => wanted.includes(t.name))
      : live;
    perServer.push({ server, tools: filtered });
  }
  return mergeStaticBindings(perServer);
}

/**
 * Resolve a dynamic binding for a query via the vector store, then hydrate the
 * chosen tools with live JSON schemas from their servers so the LLM gets
 * complete definitions.
 */
export async function resolveDynamicBinding(query, opts = {}) {
  const {
    topKServers = 5,
    topKTools = 12,
    minScore = 0.0,
    onlyRunning = true,
    maxTools = 16,
  } = opts;

  const res = await vectorSearch({
    query,
    mode: 'dynamic',
    top_k_servers: topKServers,
    top_k_tools: topKTools,
    min_score: minScore,
    filters: onlyRunning ? { status: 'running' } : {},
  });

  const wantByServer = {};
  for (const t of res.tools || []) {
    if (!t.server || !t.tool) continue;
    (wantByServer[t.server] = wantByServer[t.server] || []).push(t.tool);
  }

  // Fetch live tool schemas for the matched servers in parallel, each with a
  // short timeout so a stopped/unhealthy server (Caddy 502) can't stall the
  // turn. Cap the number of servers we probe to keep the context tight.
  const candidateServers = (res.servers || []).slice(0, topKServers);
  const settled = await Promise.allSettled(
    candidateServers.map((server) => withTimeout(mcpClient.listTools(server), 4000)),
  );
  const perServer = candidateServers.map((server, i) => {
    const r = settled[i];
    const live = r.status === 'fulfilled' && Array.isArray(r.value) ? r.value : [];
    const wanted = wantByServer[server];
    const filtered = wanted && wanted.length
      ? live.filter((t) => wanted.includes(t.name))
      : live;
    return { server, tools: filtered };
  });

  const merged = mergeStaticBindings(perServer);
  // Preserve vector rank order and cap total tools to protect context window.
  const rank = (res.tools || []).map((t) => `${t.server}::${t.tool}`);
  merged.tools.sort((a, b) => rank.indexOf(`${a.server}::${a.name}`) - rank.indexOf(`${b.server}::${b.name}`));
  merged.tools = merged.tools.slice(0, maxTools);
  merged.servers = [...new Set(merged.tools.map((t) => t.server))];
  merged.mode = 'dynamic';
  merged.notes = res.servers?.length
    ? `Matched ${merged.servers.length} server(s) via vector search`
    : 'No matching servers found';
  return merged;
}

/**
 * Namespaced identifier used for tool-call parts so the UI + orchestrator can
 * route a call back to the right server. Format: `server__tool__n`.
 */
export function encodeToolCallId(server, tool, n) {
  return `${server}__${tool}__${n}`;
}

export function decodeToolCallId(id) {
  const parts = String(id || '').split('__');
  if (parts.length >= 3) {
    return { server: parts[0], tool: parts.slice(1, -1).join('__') };
  }
  return { server: '', tool: id };
}

/** Find the owning server for a tool name within a binding. */
export function serverForTool(binding, toolName) {
  const hit = binding.tools.find((t) => t.name === toolName);
  return hit ? hit.server : (binding.servers[0] || '');
}
