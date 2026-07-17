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

  // Fetch live tool schemas for the matched servers in parallel, each with a
  // short timeout so a stopped/unhealthy server (Caddy 502) can't stall the
  // turn. This is best-effort ENRICHMENT only: a server that fails or times
  // out here must not cause its vector-matched tools to be dropped — the
  // vector result already carries the tool name + description, which is enough
  // to bind. We only use the live list to attach a precise input schema.
  const candidateServers = (res.servers || []).slice(0, topKServers);
  const settled = await Promise.allSettled(
    candidateServers.map((server) => withTimeout(mcpClient.listTools(server), 5000)),
  );
  const liveByServer = {};
  candidateServers.forEach((server, i) => {
    const r = settled[i];
    const live = r.status === 'fulfilled' && Array.isArray(r.value) ? r.value : [];
    const map = new Map();
    for (const t of live) if (t && t.name) map.set(t.name, t);
    liveByServer[server] = map;
  });

  const schemaOf = (liveTool) =>
    liveTool?.inputSchema || liveTool?.input_schema || { type: 'object', properties: {} };

  // Tier 1 — tool-level matches from the vector search, in rank order. Bound
  // straight from the vector result so a slow live fetch can never drop them;
  // enriched with the live schema when the server responded.
  const ranked = [];
  const seen = new Set();
  for (const t of res.tools || []) {
    if (!t.server || !t.tool) continue;
    const id = `${t.server}::${t.tool}`;
    if (seen.has(id)) continue;
    seen.add(id);
    const liveTool = liveByServer[t.server]?.get(t.tool);
    ranked.push({
      server: t.server,
      name: t.tool,
      description: liveTool?.description || t.description || '',
      inputSchema: schemaOf(liveTool),
      score: t.score,
    });
  }

  // Tier 2 — server-level fallback. For a server that matched only at the
  // server level (no specific tool ranked) AND whose live tools we actually
  // have, offer its tools to fill leftover budget. Precise matches always win
  // slots first, so a broadly-matching server can't crowd them out.
  const rankedServers = new Set(ranked.map((t) => t.server));
  const fallback = [];
  for (const server of candidateServers) {
    if (rankedServers.has(server)) continue;
    for (const [name, liveTool] of liveByServer[server] || []) {
      const id = `${server}::${name}`;
      if (seen.has(id)) continue;
      seen.add(id);
      fallback.push({
        server,
        name,
        description: liveTool.description || '',
        inputSchema: schemaOf(liveTool),
      });
    }
  }

  const tools = [...ranked, ...fallback].slice(0, maxTools);
  const servers = [...new Set(tools.map((t) => t.server))];
  return {
    servers,
    tools,
    mode: 'dynamic',
    notes: res.servers?.length
      ? `Matched ${servers.length} server(s) via vector search`
      : 'No matching servers found',
  };
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
