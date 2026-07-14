# PRD & Technical Spec: Chat Page (assistant-ui)

> **Status:** Implemented & deployed (v1)  
> **Owner:** MCP Farm UI  
> **Last updated:** 2026-07-02  
> **Related:** [AI-aware zero-trust gateway / FARM design](./AI-aware-zero-trust-gateway-for-MCP.md), [assistant-ui docs](https://www.assistant-ui.com/docs)
>
> Historical: [FARM-PRD-old](./FARM-PRD-old.md), [FARM-ARCHITECTURE-old](./FARM-ARCHITECTURE-old.md)

---

## Implementation status (v1)

Both chat surfaces are built on `@assistant-ui/react` with a shared runtime, and
tool binding is backed by the shared **hd-redis** Redis Stack instance under
farm-specific keys (`mcpfarm:v1:doc:*`, index `mcpfarm:idx`).

**Backend (`mcpfarm/auth-gateway/`)**

| Module | Purpose |
| --- | --- |
| `embeddings.py` | OpenAI / Ollama / offline `local` embedders (fixed `VECTOR_DIM`). |
| `vector_index.py` | RediSearch HNSW index create/upsert/search/status/delete via `FT.*`. |
| `vector_indexer.py` | README chunking, tool-schema summaries, doc building, reindex, internal MCP `tools/list`. |
| `secrets_vault.py` | Fernet-encrypted LLM key vault in SQLite (`llm_secrets`). |
| `chat_proxy.py` | Server-side single-turn multi-provider LLM proxy (keys decrypted server-side). |

New endpoints in `main.py`: `POST /chat/completions`, `POST /vectors/search`,
`GET|PUT|DELETE /llm-keys[/{provider}]`, `POST /admin/vectors/reindex`,
`GET /admin/vectors/stats`, `POST /admin/vectors/index-server/{name}`. The
`/claude` proxy now falls back to the encrypted vault key. Server start/stop/
disable update the vector `status` tag; a started server's tools are indexed.

**Frontend (`mcpfarm-ui/src/`)**

`lib/toolBinding.js`, `lib/chatOrchestrator.js` (agentic loop → assistant-ui
parts; MCP execution stays in-browser), `components/chat/useMcpChatRuntime.js`
(shared `LocalRuntime`), `components/chat/ChatThread.jsx` + `McpToolCard.jsx` +
`ProviderModelBar.jsx` + `ToolPickerDrawer.jsx` + `AutoSelectionChips.jsx`,
`components/ChatMode.jsx` (new "Chat" nav item between Catalog and Prompt), and
`components/ChatTab.jsx` reimplemented on the same runtime. `Settings.jsx` stores
provider keys in the server vault (masked prefixes only; never localStorage).

**Deploy**: `auth-gateway` joins the external `hdnet` network; config via
`REDIS_URL`, `MCPFARM_SECRETS_KEY`, `MCPFARM_VECTOR_PREFIX/INDEX`, `VECTOR_DIM`,
`EMBED_PROVIDER`, `OPENAI_API_KEY`, `OLLAMA_URL`. Populate the index once with
`POST /admin/vectors/reindex` (or set `VECTOR_AUTO_REINDEX=true`).

**Tests** (`mcpfarm/auth-gateway/tests/`, run with a venv + `pytest`): 24 tests
covering embeddings, README chunking/doc building, the encrypted vault, chat
message/response conversion (OpenAI/Claude/**Ollama**), FT.SEARCH reply parsing
for **both RESP2 and RESP3**, health-authoritative status resolution, a live
hd-redis index round-trip (create → index → KNN search → status filter → delete),
and HTTP smoke tests of every new endpoint against the booted app. Frontend
verified with `npm run build`.

### Live deployment verification (2026-07-02)

Deployed to the running farm and verified end-to-end against the shared
`hd-redis`:

- `auth-gateway` rebuilt on `hdnet`, created `mcpfarm:idx` on hd-redis, reindexed
  **400 servers → 2579 docs** (`GET /admin/vectors/stats` reports `doc_count:2579,
  dim:1536`), coexisting cleanly with the unrelated `hds:vec:idx`.
- Dynamic search via the production farm port returns sensible routing, e.g.
  "find subdomains" → `subfinder/shuffledns/assetfinder`, "scan open ports" →
  `naabu/nmap/ivre`, "brute force login credentials" → `hydra/medusa/bully`.
- Encrypted vault round-trip (`PUT/GET/DELETE /llm-keys`) confirmed: DB stores
  only Fernet ciphertext (`gAAAAAB…`), zero plaintext leakage, masked prefix
  returned to the UI.
- **Full agentic loop** with Ollama `qwen3-coder`: user question → model emits
  `whois_lookup({domain:"example.com"})` → executed live against `whois-mcp` →
  result fed back → correct final answer (registrar, creation/expiry dates,
  nameservers). Confirms the browser wire contract end-to-end.

Deployment fixes made during verification:

1. **Caddy routing source of truth** — the gateway rebuilds the whole Caddyfile
   from `caddy_reload.py` and pushes it via the admin API, so the new
   `/chat/*`, `/vectors/*`, `/llm-keys*` handles (and `PUT` in CORS) were added
   there, not just the static `Caddyfile`.
2. **RESP3 support** — redis-py ≥ 8 negotiates RESP3, so `FT.SEARCH` returns a
   map; `vector_index._parse_search` now handles both the RESP3 dict and the
   RESP2 array, and the built-in `FT.SEARCH` response callback is overridden with
   a passthrough so the raw reply reaches our parser.
3. **Ollama tool-call format** — Ollama's `/api/chat` expects tool-call
   `arguments` as a JSON object (not a stringified JSON) and a non-null assistant
   `content`; added `chat_proxy._messages_to_ollama`.
4. **Health-authoritative status** — `vector_indexer._status_of` now trusts
   `health_ok` rather than the optimistic DB `status`, so the vector `status` tag
   is accurate and tool indexing only targets live servers.

---

## Table of contents

1. [Product requirements (PRD)](#1-product-requirements-prd)
2. [Technical specification](#2-technical-specification)
3. [Tool binding modes](#3-tool-binding-modes)
4. [Redis vector index](#4-redis-vector-index)
5. [API specification](#5-api-specification)
6. [Frontend specification](#6-frontend-specification)
7. [Per-server Chat tab (assistant-ui)](#7-per-server-chat-tab-assistant-ui)
8. [LLM key storage](#8-llm-key-storage)
9. [Implementation phases](#9-implementation-phases)
10. [Testing plan](#10-testing-plan)
11. [Open questions](#11-open-questions)

---

## 1. Product requirements (PRD)

### 1.1 Summary

This spec covers **two chat surfaces**, both rebuilt on [assistant-ui](https://www.assistant-ui.com/) so they share one runtime, one set of thread/tool primitives, and one orchestration layer:

1. **Chat page** — a new top-level, ChatGPT-style page for cross-server conversations with dynamic or static tool binding.
2. **Per-server Chat tab** — the existing `ChatTab` inside `ServerDetail` (Catalog → server → Chat), reimplemented on assistant-ui. It is scoped to a single server (binding is always that server's tools) but reuses the same components and orchestrator.

The **Chat page** sits in the top navigation **between Catalog and Prompt**:

```
Catalog | Chat | Prompt | Nova
```

Two tool-binding strategies are supported on the Chat page:

| Mode | Label | Behavior |
|------|-------|----------|
| **Dynamic** | Auto | Vector search on hd-redis selects servers/tools per message |
| **Static** | Manual | User explicitly selects servers and/or tools before sending |

### 1.2 Problem statement

Today the farm has three chat-like surfaces with overlapping behavior:

| Surface | Limitation |
|---------|------------|
| **Prompt** | Claude-only; binds all running servers or a server subset; no semantic tool selection |
| **Nova** | Claude-only; persona + avatar; loads all health-running tools |
| **Chat tab** (ServerDetail) | Single-server; multi-LLM; hand-rolled message list and tool-call loop; no streaming, edit, regenerate, or cancel; duplicate chat code diverging from other surfaces |

None provide a polished, ChatGPT-grade UX with intelligent tool routing at farm scale (~400 servers). Passing every tool schema to the LLM is impossible within context limits. Users need either automatic relevance-based binding or explicit control.

The **per-server Chat tab** already delivers the right scope (one server, multi-LLM) but is built on bespoke message rendering (`ChatMessage`, manual `while` tool loop in `ChatTab.jsx`). Rebuilding it on assistant-ui removes duplicate code, gives it the same streaming/edit/cancel UX as the Chat page, and lets both surfaces share `chatOrchestrator.js`, the MCP Tool UI toolkit, and provider/model selection.

### 1.3 Goals

| ID | Goal | Success criteria |
|----|------|------------------|
| G1 | World-class chat UX | Streaming, markdown, tool-call UI, edit/regenerate, cancel — via assistant-ui |
| G2 | Dynamic tool binding | User query → vector search → relevant tools bound in &lt; 500 ms (p95, excluding embed API) |
| G3 | Static tool binding | User can select servers/tools; only selected tools are passed to the LLM |
| G4 | Multi-LLM support | All providers already in Settings (Claude, OpenAI, Ollama, Bedrock, Azure, OpenRouter, Grok, Gemini) |
| G5 | Secure key handling | LLM keys encrypted at rest on auth-gateway; browser never stores plaintext keys after migration |
| G6 | Farm-scale catalog | READMEs, server names, display names, categories, and tool metadata vectorized in hd-redis |
| G7 | Unified per-server Chat tab | `ChatTab` reimplemented on assistant-ui; shares runtime, orchestrator, and Tool UI with the Chat page; single-server binding preserved |

### 1.4 Non-goals (v1)

- Replacing Prompt or Nova modes
- Removing the per-server Chat tab (it is reimplemented, not removed) or changing its single-server scope (no dynamic/vector binding inside the tab)
- Thread persistence across devices (localStorage-only in v1; server persistence in v2)
- File attachments / vision models
- Voice / realtime audio
- Human-in-the-loop approval gates for destructive tools (v2)
- Per-user multi-tenancy (single farm operator in v1)

### 1.5 User personas

| Persona | Need | Primary binding mode |
|---------|------|----------------------|
| **Analyst** | "Scan this host for open ports" without knowing which MCP server to use | Dynamic |
| **Power user** | Run nmap + naabu only, nothing else | Static |
| **Operator** | Verify a specific tool after catalog changes | Static |
| **Developer** | Iterate on one server's tools while chatting | Static (single server) |

### 1.6 User stories

#### Navigation & shell

- **US-1:** As a user, I see **Chat** in the header between Catalog and Prompt so I can open the default conversational interface.
- **US-2:** As a user, I see a thread list (new chat, recent threads) and a main message area similar to ChatGPT.

#### Dynamic binding

- **US-3:** As a user in **Auto** mode, when I send a message the system selects relevant MCP tools without my input.
- **US-4:** As a user, I see which servers/tools were auto-selected for a turn (collapsible chip strip above the assistant reply).
- **US-5:** As a user, if no running server matches my query, I get a clear message suggesting I start a server from Catalog.

#### Static binding

- **US-6:** As a user in **Manual** mode, I open a tool picker and select one or more servers and/or individual tools.
- **US-7:** As a user, I can pin my static selection for the entire thread so I do not re-select on every message.
- **US-8:** As a user, I can override pinned selection for a single message via a "Use selection for this message only" toggle.

#### Chat experience

- **US-9:** As a user, I can choose LLM provider and model from a composer toolbar dropdown.
- **US-10:** As a user, I see streaming assistant text and structured tool-call cards (args, running, result, error).
- **US-11:** As a user, I can cancel an in-flight generation.
- **US-12:** As a user, I can edit my last message and regenerate the assistant response.

#### Per-server Chat tab

- **US-13:** As a user on a server's detail page, I open the **Chat** tab and get the same assistant-ui thread and Tool UI as the main Chat page, scoped to that one server.
- **US-14:** As a user, I choose provider and model in the tab; binding is fixed to the current server (no picker, no vector search).
- **US-15:** As a user, if the server is stopped, the composer is disabled with a prompt to start it from Catalog.
- **US-16:** As a user, I still get sample prompts derived from the server's tools when the thread is empty.

#### Settings & security

- **US-17:** As a user, I save LLM API keys in Settings; they are encrypted on the server and shown only as masked prefixes in the UI.
- **US-18:** As an admin, I can trigger a full vector reindex from an admin endpoint.

### 1.7 UX requirements

#### Layout

```
┌──────────────────────────────────────────────────────────────────────────┐
│  MCP Farm          Catalog | [Chat] | Prompt | Nova          [Settings]  │
├────────────┬─────────────────────────────────────────────────────────────┤
│ Thread     │  ┌─ Binding bar ─────────────────────────────────────────┐ │
│ list       │  │ [Auto ▾]  Auto-selected: nmap-mcp · naabu-mcp  [Edit] │ │
│            │  └───────────────────────────────────────────────────────┘ │
│ + New chat │                                                             │
│            │  Messages (assistant-ui Thread)                             │
│ Today      │    User: Scan 10.0.0.1 for open ports                     │
│  · Thread1 │    Assistant: I'll run an nmap scan...                     │
│            │    ▼ nmap-mcp → run_nmap                                    │
│ Yesterday  │                                                             │
│  · Thread2 │  ┌─────────────────────────────────────────────────────┐   │
│            │  │ Provider: Claude ▾  Model: sonnet-4-6 ▾             │   │
│            │  │ Message...                                          │   │
│            │  └─────────────────────────────────────────────────────┘   │
├────────────┴─────────────────────────────────────────────────────────────┤
│  (Manual mode) Tool picker drawer — servers → tools checkboxes           │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Visual principles

- Match existing MCP Farm theme (`index.css` CSS variables, dark/light).
- No decorative emoji in Chat mode UI copy or labels.
- Minimal chrome: binding bar, thread, composer. No avatar (reserved for Nova).
- Tool calls use assistant-ui Tool UI with collapsible JSON/result panels.

#### Binding mode toggle

| UI control | Values | Default |
|------------|--------|---------|
| Binding mode | `Auto` (dynamic) / `Manual` (static) | `Auto` |
| Pin selection (manual only) | on / off | on |
| Provider | from `LLM_PROVIDERS` | last used or Claude |
| Model | provider-specific list | provider default |

### 1.8 Acceptance criteria (v1 ship)

1. Chat nav item renders and loads without regression to Catalog, Prompt, Nova.
2. Auto mode: message "scan example.com for open ports" binds nmap-mcp or equivalent when running.
3. Manual mode: user selects `nmap-mcp` only; no other server tools appear in the LLM context.
4. Streaming works for Claude and at least one OpenAI-compatible provider.
5. Tool execution routes through existing `mcpClient.callTool()` with namespaced tool names.
6. LLM keys stored encrypted on auth-gateway; Chat calls go through `/chat/completions` proxy.
7. Vector index contains all server READMEs and metadata; tool docs for running servers.
8. Per-server Chat tab renders the assistant-ui thread scoped to that server, with streaming and tool cards, and no regression to other `ServerDetail` tabs. Old `ChatMessage`/manual loop code in `ChatTab.jsx` is removed.

---

## 2. Technical specification

### 2.1 Architecture overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│  mcpfarm-ui                                                             │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  ChatMode.jsx                                                     │  │
│  │  ├── AssistantRuntimeProvider (useLocalRuntime)                   │  │
│  │  ├── ChatModelAdapter → chatOrchestrator.js                       │  │
│  │  ├── BindingBar (mode toggle + selection chips)                     │  │
│  │  ├── ToolPickerDrawer (static mode)                               │  │
│  │  ├── ThreadList + Thread (assistant-ui)                           │  │
│  │  └── McpToolToolkit (Tool UI renderers)                           │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│         │ REST                           │ MCP JSON-RPC                 │
└─────────┼────────────────────────────────┼────────────────────────────┘
          ▼                                ▼
┌─────────────────────┐          ┌─────────────────────┐
│  auth-gateway       │          │  Caddy → MCP        │
│  ├── /vectors/*     │          │  containers         │
│  ├── /chat/*        │          └─────────────────────┘
│  ├── /admin/llm-keys│
│  └── vector_indexer │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  hd-redis           │
│  (Redis Stack)      │
│  RediSearch + HNSW  │
└─────────────────────┘
```

### 2.2 Technology choices

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Chat UI | `@assistant-ui/react` + `LocalRuntime` | Vite/React app (not Next.js); full control over MCP orchestration |
| Thread components | assistant-ui `Thread`, `ThreadList` | ChatGPT-grade UX out of the box |
| Tool rendering | assistant-ui `defineToolkit` backend entries | MCP tools execute externally; UI-only renderers |
| Vector DB | **hd-redis** (Redis Stack, RediSearch HNSW) | Already running; hybrid KNN + TAG filters |
| Embeddings | OpenAI `text-embedding-3-small` (1536 dim) | Server-side; Ollama fallback optional |
| LLM calls | auth-gateway `/chat/completions` | Encrypt keys server-side; avoid browser plaintext |
| MCP protocol | Existing `mcp.js` | Session management, `tools/list`, `tools/call` unchanged |
| Tool routing | Extend `claude.js` patterns → `chatOrchestrator.js` | Provider-agnostic agentic loop via `llm.js` |

### 2.3 New files

#### Frontend (`mcpfarm-ui/`)

| File | Purpose |
|------|---------|
| `src/components/ChatMode.jsx` | Page shell, runtime provider, layout |
| `src/components/chat/BindingBar.jsx` | Auto/Manual toggle, selection chips, pin toggle |
| `src/components/chat/ToolPickerDrawer.jsx` | Static server/tool tree with search |
| `src/components/chat/AutoSelectionChips.jsx` | Shows dynamic binding results per turn |
| `src/components/chat/ChatThread.jsx` | Shared assistant-ui `Thread` wrapper + composer toolbar (provider/model). Used by Chat page and per-server tab |
| `src/components/chat/useMcpChatRuntime.js` | Hook that builds the `LocalRuntime` + `ChatModelAdapter` from a binding resolver. Parametrized so the per-server tab passes a fixed single-server resolver |
| `src/components/assistant-ui/thread.tsx` | assistant-ui thread (from CLI or copied) |
| `src/components/assistant-ui/thread-list.tsx` | Thread sidebar |
| `src/components/assistant-ui/tool-fallback.tsx` | Default MCP tool card |
| `src/lib/chatOrchestrator.js` | Binding resolution + agentic loop adapter |
| `src/lib/toolBinding.js` | Dynamic/static binding logic, types |
| `src/lib/chatThreads.js` | localStorage thread persistence (v1) |
| `src/lib/mcpToolToolkit.js` | `defineToolkit` entries for Tool UI |

#### Backend (`mcpfarm/auth-gateway/`)

| File | Purpose |
|------|---------|
| `vector_index.py` | Redis index create, HSET docs, FT.SEARCH |
| `vector_indexer.py` | Batch index READMEs, server meta, tools |
| `embeddings.py` | Embed text via OpenAI or Ollama |
| `secrets_vault.py` | Fernet encrypt/decrypt LLM keys |
| `chat_proxy.py` | `/chat/completions` multi-provider proxy |

### 2.4 Modified files

| File | Change |
|------|--------|
| `mcpfarm-ui/src/App.jsx` | Add `chat` mode between `manual` and `prompt` |
| `mcpfarm-ui/package.json` | Add `@assistant-ui/react`, `@assistant-ui/react-markdown`, `zustand` |
| `mcpfarm-ui/src/lib/api.js` | Add vector search, chat completions, llm-keys API |
| `mcpfarm-ui/src/components/Settings.jsx` | Save keys via server vault; show masked prefixes |
| `mcpfarm-ui/src/components/ChatTab.jsx` | **Reimplemented** on assistant-ui: replace `ChatMessage` list + manual tool loop with `ChatThread` + `useMcpChatRuntime` scoped to one server. Keep tool discovery and sample-prompt helpers |
| `mcpfarm-ui/src/components/ServerDetail.jsx` | No prop changes required; still renders `<ChatTab serverName tools isRunning onLoadTools />` (see §7.3) |
| `mcpfarm/auth-gateway/main.py` | Mount new routers; env vars for Redis |
| `mcpfarm/docker-compose.yml` | `REDIS_URL`, `MCPFARM_SECRETS_KEY`, link to hd-redis network |

---

## 3. Tool binding modes

### 3.1 Concepts

| Term | Definition |
|------|------------|
| **Binding** | The set of `{ serverName, tool }` pairs passed to the LLM for one turn |
| **Turn** | One user message → agentic loop (may include multiple tool calls) → final assistant text |
| **Thread** | A conversation with ordered turns |
| **Tool identity** | LLM-facing name: `{serverName}__{tool_name}` (hyphens → underscores) per `claude.js` |

### 3.2 Dynamic binding (Auto)

**Trigger:** User sends a message while binding mode is `Auto`.

**Flow:**

```
1. Collect query text:
   - Primary: current user message
   - Optional context: last user message (if follow-up pronouns detected)

2. POST /vectors/search
   Body: { query, mode: "dynamic", filters: { status: "running" }, top_k_servers: 5, top_k_tools: 20 }

3. auth-gateway:
   a. Embed query → 1536-dim vector
   b. Stage 1: KNN on doc_type IN (server, alias, readme) → top 5 servers
   c. Stage 2: KNN on doc_type=tool AND server IN (stage1) → top 20 tools
   d. Deduplicate by (server, tool); attach score

4. Frontend receives BindingResult:
   { servers: [...], tools: [{ server, tool, score, description }], query_ms }

5. For each server in result:
   - If tools already in index with full schema → use cached schema
   - Else mcpClient.listTools(server) → merge

6. Pass binding.tools to chatOrchestrator → LLM agentic loop

7. UI: show AutoSelectionChips with server/tool names and scores (collapsed by default)
```

**Parameters (configurable via env / admin):**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `top_k_servers` | 5 | Max servers after stage 1 |
| `top_k_tools` | 20 | Max tools after stage 2 |
| `min_score` | 0.72 | Drop matches below cosine similarity threshold |
| `max_tools_to_llm` | 25 | Hard cap sent to LLM (truncate by score) |
| `include_readme_chunks` | true | Stage 1 searches readme chunks for server discovery |

**Fallback behavior:**

| Condition | Action |
|-----------|--------|
| Redis unavailable | Fall back to keyword search on server names (Catalog logic); warn in binding bar |
| No results above threshold | Show "No matching tools. Try Manual mode or start servers in Catalog." |
| Server in results but stopped | Filtered by `status:running` tag; never bound |
| `tools/list` fails for server | Skip server; log warning; continue with remaining |

**Optional enhancement (v1.1):** `@mention` in composer boosts mentioned server +5 score or bypasses vector search entirely.

### 3.3 Static binding (Manual)

**Trigger:** User sends a message while binding mode is `Manual`.

**Selection model:**

```
StaticSelection {
  servers: string[]           // selected server names (e.g. ["nmap-mcp"])
  tools: ToolRef[]            // explicit tool picks (optional, granular)
  pinToThread: boolean        // if true, reuse for all messages in thread
}

ToolRef {
  server: string
  tool: string                // MCP tool name from tools/list
}
```

**Resolution rules:**

| User selection | Resolved binding |
|----------------|------------------|
| Servers only, no tools checked | All tools from `tools/list` for each selected server |
| Specific tools checked | Only those tools |
| Empty selection | Block send; show validation error |
| Pinned + new message | Reuse same StaticSelection |
| Unpinned | Require selection (or last selection pre-filled in picker) |

**Flow:**

```
1. User opens ToolPickerDrawer
2. Tree: Server (checkbox) → expand → Tool (checkbox)
   - Only running/healthy servers selectable (grey out others with "Start in Catalog")
   - Search filters server and tool names/descriptions (client-side)

3. User checks nmap-mcp + naabu-mcp (server level)
   OR checks run_nmap under nmap-mcp only (tool level)

4. On Send:
   a. Resolve StaticSelection → BindingResult (no vector call)
   b. Fetch tools/list for any server without cached tool schemas
   c. Filter to selected tools
   d. Pass to chatOrchestrator

5. UI: BindingBar shows "Manual: nmap-mcp (3 tools)" with Edit button
```

**Static selection persistence:**

| Scope | Storage (v1) |
|-------|--------------|
| Per thread | `chatThreads.js` → `thread.staticSelection` when `pinToThread: true` |
| Per message | Passed in adapter `runConfig.custom.staticSelection` |
| Default for new thread | Empty; user must select or switch to Auto |

### 3.4 Mode interaction matrix

| Binding mode | Vector search | User picker | Pin supported |
|--------------|---------------|-------------|---------------|
| Auto | Yes | Hidden (view-only chips after send) | N/A |
| Manual | No | Required (unless pinned) | Yes |

**Hybrid (v1.1, not v1):** Auto mode with manual override — user clicks "Edit" on auto chips and locks specific tools for next turn.

### 3.5 BindingResult (shared type)

```typescript
interface BindingResult {
  mode: "dynamic" | "static";
  servers: string[];
  tools: BoundTool[];
  meta: {
    query_ms?: number;
    vector_search?: boolean;
    truncated?: boolean;      // true if max_tools_to_llm applied
    warnings?: string[];
  };
}

interface BoundTool {
  server: string;
  tool: {
    name: string;
    description?: string;
    inputSchema?: object;
  };
  score?: number;             // dynamic only
  anthropicName: string;      // nmap_mcp__run_nmap
}
```

### 3.6 Agentic loop (post-binding)

Reuses and generalizes logic from `claude.js` and `llm.js`:

```
chatOrchestrator.runTurn({
  messages,
  binding: BindingResult,
  provider,
  model,
  abortSignal,
  onEvent,   // stream text, tool_call, tool_result
})

Loop (max 10 iterations):
  1. Call LLM with messages + bound tool schemas
  2. If text only → yield final text, exit
  3. For each tool_use block:
     a. Map anthropicName → { serverName, toolName }
     b. mcpClient.callTool(serverName, toolName, args)
     c. Append tool_result to messages
  4. Continue until stop or max iterations
```

Provider routing via existing `llm.js` `callLLM()` with `toolFormat` (`claude` | `openai` | `ollama`).

---

## 4. Redis vector index

### 4.1 Infrastructure

| Item | Value |
|------|-------|
| Service | `hd-redis` (Redis Stack, Docker) |
| Connection | `REDIS_URL=redis://hd-redis:6379` (auth-gateway env) |
| Module required | RediSearch (`MODULE LIST` → `search`) |
| Key prefix | `mcpfarm:v1:doc:` |
| Index name | `mcpfarm:idx` |

Connect auth-gateway to the same Docker network as hd-redis, or expose hd-redis port to the host.

### 4.2 Index schema

```
FT.CREATE mcpfarm:idx
  ON HASH
  PREFIX 1 mcpfarm:v1:doc:
  SCHEMA
    text        TEXT
    server      TAG
    tool        TAG
    doc_type    TAG
    category    TAG
    status      TAG
    display_name TEXT
    chunk_index NUMERIC
    embedding   VECTOR HNSW 12
      TYPE FLOAT32
      DIM 1536
      DISTANCE_METRIC COSINE
      M 16
      EF_CONSTRUCTION 200
      EF_RUNTIME 50
```

Reference: [Redis vector search docs](https://redis.io/docs/latest/develop/ai/search-and-query/vectors/)

### 4.3 Document types

| doc_type | Redis key pattern | Indexed text |
|----------|-------------------|--------------|
| `server` | `mcpfarm:v1:doc:{server}:meta` | `{name} {display_name} {category_label} {short_description}` |
| `alias` | `mcpfarm:v1:doc:{server}:alias:{n}` | Common synonyms, e.g. "port scan", "network mapper" |
| `readme` | `mcpfarm:v1:doc:{server}:readme:{chunk}` | README section chunk (## heading + body) |
| `tool` | `mcpfarm:v1:doc:{server}:tool:{tool}` | `{tool_name} {description} {schema_summary}` |

**Metadata fields on every doc:**

- `server` — canonical name, e.g. `nmap-mcp`
- `tool` — empty for non-tool docs; tool name for `doc_type=tool`
- `category` — from `port-map.json`
- `status` — `running` | `stopped` | `disabled` (updated on server lifecycle events)
- `display_name` — name without `-mcp` suffix

### 4.4 Indexing pipeline

| Trigger | Action |
|---------|--------|
| Farm boot / `POST /admin/vectors/reindex` | Full reindex: all servers from SQLite/`port-map.json` + READMEs |
| Server start + health_ok | Fetch `tools/list`; upsert tool docs; set `status=running` |
| Server stop / disable | Set `status=stopped` or delete tool docs |
| README change (admin reload) | Re-chunk and upsert readme docs for that server |

**README chunking:**

- Split on `##` headings
- Target 400–600 tokens per chunk
- Prepend: `Server: {name} ({display_name}). Category: {category}.`
- Max 20 chunks per server

**Tool schema summary:**

- Flatten `inputSchema.properties` to `param: type` list
- Truncate description to 500 chars

### 4.5 Search queries

**Stage 1 — server discovery:**

```
FT.SEARCH mcpfarm:idx
  "(@doc_type:{server|alias|readme}) (@status:{running})=>[KNN 8 @embedding $vec EF_RUNTIME 50]"
  PARAMS 2 vec <bytes>
  SORTBY __embedding_score
  RETURN 2 server display_name
  DIALECT 2
```

Aggregate by `server`, take top 5 by best chunk score.

**Stage 2 — tool ranking:**

```
FT.SEARCH mcpfarm:idx
  "(@doc_type:{tool}) (@status:{running}) (@server:{nmap-mcp|naabu-mcp|...})=>[KNN 20 @embedding $vec EF_RUNTIME 50]"
  PARAMS 2 vec <bytes>
  SORTBY __embedding_score
  RETURN 4 server tool text
  DIALECT 2
```

### 4.6 Embedding service

```python
# embeddings.py
async def embed_texts(texts: list[str]) -> list[list[float]]:
    # Primary: OpenAI text-embedding-3-small (1536)
    # Fallback: Ollama nomic-embed-text at OLLAMA_URL
```

Env: `OPENAI_API_KEY` or `OLLAMA_URL` on auth-gateway (not in browser).

---

## 5. API specification

### 5.1 Vector search

**`POST /vectors/search`**

Auth: Bearer farm API key.

Request:

```json
{
  "query": "scan example.com for open ports",
  "mode": "dynamic",
  "filters": {
    "status": "running",
    "categories": []
  },
  "top_k_servers": 5,
  "top_k_tools": 20,
  "min_score": 0.72
}
```

Response:

```json
{
  "mode": "dynamic",
  "servers": ["nmap-mcp", "naabu-mcp"],
  "tools": [
    {
      "server": "nmap-mcp",
      "tool": "run_nmap",
      "description": "Run nmap with CLI arguments",
      "score": 0.89,
      "input_schema": { "type": "object", "properties": {} }
    }
  ],
  "meta": {
    "query_ms": 42,
    "embed_ms": 120,
    "truncated": false
  }
}
```

### 5.2 Vector admin

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/admin/vectors/reindex` | Full rebuild (admin secret) |
| `GET` | `/admin/vectors/stats` | Doc counts, index info, last reindex time |
| `POST` | `/admin/vectors/index-server/{name}` | Index one server |

### 5.3 Chat completions proxy

**`POST /chat/completions`**

Auth: Bearer farm API key.

Request:

```json
{
  "provider": "claude",
  "model": "claude-sonnet-4-6",
  "messages": [],
  "tools": [],
  "stream": true,
  "max_tokens": 8192
}
```

- Gateway decrypts provider key from vault.
- Streams SSE back to client in provider-native or normalized format.
- For v1 simplification: non-streaming JSON also supported; frontend adapter handles streaming simulation if needed.

### 5.4 LLM key vault

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/llm-keys` | List configured providers (masked: `sk-...abcd`) |
| `PUT` | `/llm-keys/{provider}` | Upsert encrypted key |
| `DELETE` | `/llm-keys/{provider}` | Remove key |

Encryption: Fernet (AES-128-CBC + HMAC) with `MCPFARM_SECRETS_KEY` env var (32-byte url-safe base64).

Storage: SQLite table `llm_secrets (provider TEXT PRIMARY KEY, ciphertext BLOB, key_prefix TEXT, updated_at)`.

Migration: On first `PUT`, optionally import from browser localStorage if client sends `migrate: true` one-time.

---

## 6. Frontend specification

### 6.1 App.jsx integration

```javascript
const MODES = [
  { id: 'manual', label: 'Catalog' },
  { id: 'chat', label: 'Chat' },      // NEW
  { id: 'prompt', label: 'Prompt' },
  { id: 'agent', label: 'Nova' },
];

// main panel
{mode === 'chat' && <ChatMode servers={servers} />}
```

### 6.2 ChatMode component structure

```jsx
<ChatMode servers={servers}>
  <AssistantRuntimeProvider runtime={runtime} aui={aui}>
    <div className="chat-layout">
      <ThreadList />
      <div className="chat-main">
        <BindingBar
          mode={bindingMode}
          onModeChange={setBindingMode}
          selection={currentBinding}
          pinToThread={pinToThread}
          onPinChange={setPinToThread}
          onEditManual={() => setPickerOpen(true)}
        />
        <Thread />
        <ComposerToolbar provider={provider} model={model} />
      </div>
      <ToolPickerDrawer
        open={pickerOpen}
        servers={servers}
        selection={staticSelection}
        onChange={setStaticSelection}
        onClose={() => setPickerOpen(false)}
      />
    </div>
  </AssistantRuntimeProvider>
</ChatMode>
```

### 6.3 LocalRuntime adapter

The adapter is built by a shared hook, `useMcpChatRuntime`, which takes a **binding resolver** function. The Chat page passes a resolver that switches on Auto/Manual; the per-server Chat tab (§7) passes a fixed single-server resolver. Everything downstream (streaming, tool execution, Tool UI) is identical.

```javascript
// useMcpChatRuntime.js
export function useMcpChatRuntime({ resolveBinding, getProviderModel }) {
  const adapter = useMemo(() => ({
    async *run({ messages, abortSignal, runConfig }) {
      const userText = lastUserMessage(messages);
      const { provider, model } = getProviderModel();

      // 1. Resolve binding (Auto vs Manual vs fixed single-server)
      const binding = await resolveBinding({ userText, runConfig, messages });

      // 2. Emit binding metadata (for AutoSelectionChips; ignored by the tab)
      yield { metadata: { custom: { binding } } };

      // 3. Shared agentic loop with streaming
      for await (const event of chatOrchestrator.streamTurn({
        messages, binding, provider, model, abortSignal,
      })) {
        if (event.type === 'text') {
          yield { content: [{ type: 'text', text: event.text }] };
        }
        if (event.type === 'tool_call') {
          // accumulate in Map outside loop (per assistant-ui docs)
          yield { content: [...accumulatedToolCalls, ...] };
        }
      }
    },
  }), [resolveBinding, getProviderModel]);

  return useLocalRuntime(adapter);
}
```

**Chat page resolver:**

```javascript
const resolveBinding = ({ userText, runConfig }) => {
  const mode = runConfig.custom?.bindingMode ?? 'dynamic';
  return mode === 'dynamic'
    ? resolveDynamicBinding(userText)              // vector search
    : resolveStaticBinding(runConfig.custom?.staticSelection, servers);
};
```

**Per-server tab resolver** (see §7.2): always binds the current server's tools, no vector search, no picker.

### 6.4 ToolPickerDrawer (static mode)

**Data loading:**

- Server list from `servers` prop filtered by `isServerRunning()`
- On server expand: `mcpClient.listTools(serverName)` (lazy load, cache in component state)
- Client-side search across server name, display name, tool name, description

**UI states:**

| State | Display |
|-------|---------|
| Loading tools | Skeleton under expanded server |
| Server stopped | Disabled row, tooltip "Start in Catalog" |
| No tools | "No tools reported" |
| Selection count | Footer: "3 tools from 2 servers" |

**Checkbox logic:**

- Check server → select all tools (when loaded)
- Uncheck server → deselect all its tools
- Partial tool selection → server shows indeterminate checkbox

### 6.5 Tool UI (MCP)

Generic renderer for all MCP tools:

```javascript
// mcpToolToolkit.js
defineToolkit({
  // Dynamic registration: one backend entry per bound tool per turn
  // Pattern: render-only, type: "backend"
  mcp_tool_fallback: {
    type: "backend",
    render: McpToolCallCard,  // server, tool, args, status, result
  },
});
```

`McpToolCallCard` reuses `ToolResultContent.jsx` for result bodies.

### 6.6 Thread persistence (v1)

`chatThreads.js` stores in localStorage:

```json
{
  "threads": [
    {
      "id": "uuid",
      "title": "Port scan on 10.0.0.1",
      "createdAt": "ISO",
      "updatedAt": "ISO",
      "bindingMode": "dynamic",
      "staticSelection": null,
      "pinToThread": false,
      "provider": "claude",
      "model": "claude-sonnet-4-6",
      "messages": []
    }
  ],
  "activeThreadId": "uuid"
}
```

assistant-ui `LocalRuntime` `initialMessages` loaded per thread switch.

### 6.7 Dependencies

```json
{
  "@assistant-ui/react": "^0.14.x",
  "@assistant-ui/react-markdown": "^0.14.x",
  "remark-gfm": "^4.0.1",
  "zustand": "^5.x"
}
```

Install thread components:

```bash
npx assistant-ui@latest add thread thread-list
```

---

## 7. Per-server Chat tab (assistant-ui)

### 7.1 Purpose and scope

The **Chat** tab inside `ServerDetail` (Catalog → open a server → Chat) is reimplemented on assistant-ui. It reuses the Chat page's runtime hook, orchestrator, and Tool UI, but is permanently scoped to the single server whose detail page is open.

| Property | Chat page | Per-server Chat tab |
|----------|-----------|---------------------|
| Binding | Dynamic or Static (user choice) | **Fixed:** always the current server's tools |
| Vector search | Yes (Auto mode) | No |
| Tool picker / binding bar | Yes | No |
| Thread list | Yes | No — single ephemeral thread per tab mount |
| Provider/model picker | Yes | Yes (unchanged from current tab) |
| Tool discovery button | No (implicit) | Yes (kept — explicit `tools/list`) |
| Sample prompts | Suggestions API (v1.1) | Yes (kept — `getSamplePrompts`) |

### 7.2 Current implementation being replaced

`ChatTab.jsx` today (see file) contains, and will remove:

- `ChatMessage` component with hand-rolled `user` / `assistant` / `tool-call` / `tool-result` / `error` rendering
- A manual `while (rounds < MAX_TOOL_ROUNDS)` agentic loop calling `chatCompletion()` from `llm.js`
- Manual per-provider tool-message shaping (`claude` / `openai` / fallback branches)
- Custom message list, thinking dots, scroll-to-bottom, and input bar

All of the above is superseded by assistant-ui `Thread` + the shared `chatOrchestrator.streamTurn` loop.

**Kept from the current tab:**

- `discoverTools()` → `mcpClient.listTools(serverName)` and the `onLoadTools` callback that lifts tools into `ServerDetail`
- `getSamplePrompts(serverName, tools)` helper (rendered via assistant-ui suggestion/empty-state slot)
- Provider/model selectors (moved into the shared composer toolbar)
- Running/stopped gating of the composer

### 7.3 New structure

```jsx
// ChatTab.jsx (reimplemented)
export default function ChatTab({ serverName, tools, isRunning, onLoadTools }) {
  const [provider, setProvider] = useState('ollama');
  const [model, setModel] = useState('');
  const [localTools, setLocalTools] = useState(tools || []);

  // Fixed single-server binding — no vector search, no picker
  const resolveBinding = useCallback(async () => {
    const toolList = localTools.length ? localTools
      : await mcpClient.listTools(serverName);
    return toStaticBinding(serverName, toolList);   // toolBinding.js helper
  }, [serverName, localTools]);

  const runtime = useMcpChatRuntime({
    resolveBinding,
    getProviderModel: () => ({ provider, model }),
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="chat-tab">
        <ComposerToolbar
          provider={provider} model={model}
          onProvider={setProvider} onModel={setModel}
          onDiscover={discoverTools}          // keeps explicit discovery
          toolCount={localTools.length}
          disabled={!isRunning}
        />
        <ChatThread
          disabled={!isRunning}
          emptyState={
            <ServerChatEmptyState
              serverName={serverName}
              isRunning={isRunning}
              samplePrompts={getSamplePrompts(serverName, localTools)}
            />
          }
        />
      </div>
    </AssistantRuntimeProvider>
  );
}
```

- `ServerDetail.jsx` keeps rendering `<ChatTab serverName tools isRunning onLoadTools />` exactly as it does at line ~756 today — **no prop changes**.
- `ChatThread` and `ComposerToolbar` are the same shared components used by `ChatMode`.
- No `ThreadList` is rendered in the tab; the thread is ephemeral to the tab's lifetime (v1). Optional: persist per-server threads via `chatThreads.js` keyed by `serverName` in v1.1.

### 7.4 Binding helper

```javascript
// toolBinding.js
export function toStaticBinding(serverName, tools) {
  return {
    mode: 'static',
    servers: [serverName],
    tools: tools.map((t) => ({
      server: serverName,
      tool: t,
      anthropicName: `${serverName}__${t.name}`.replace(/-/g, '_'),
    })),
    meta: { vector_search: false },
  };
}
```

This is the same `BindingResult` shape defined in §3.5, so `chatOrchestrator.streamTurn` treats tab turns and Chat-page turns identically.

### 7.5 Behavior parity checklist

| Current behavior | Reimplemented behavior |
|------------------|------------------------|
| Discover tools button | Kept in composer toolbar; updates binding + `onLoadTools` |
| Stopped server disables input | Composer disabled with "Start it to use chat" empty state |
| Sample prompts populate input | Rendered in empty state; click sends or fills composer |
| Multi-round tool calls | Handled by shared orchestrator (max 10 rounds) |
| Markdown assistant output | assistant-ui markdown renderer |
| Tool call + result cards | assistant-ui Tool UI (`McpToolCallCard`) |
| Provider/model selection | Kept; drives `getProviderModel()` |
| No streaming | **New:** streaming, plus cancel and edit/regenerate for free |

### 7.6 CSS

Existing `.chat-tab`, `.chat-provider-bar`, `.chat-*` classes in `index.css` are largely reused for the toolbar and container. assistant-ui `Thread` internals are styled to match via the shared `ChatThread` wrapper (same tokens as the Chat page), so the tab does not introduce a separate visual theme.

---

## 8. LLM key storage

### 8.1 Current state (pre-migration)

All keys in browser `localStorage` as **plaintext** (`hd_claude_key`, `hd_openai_key`, etc.). Password inputs only obscure on screen.

### 8.2 Target state

| Location | Content |
|----------|---------|
| Browser | Provider preference, model preference, masked prefix only |
| auth-gateway SQLite | Fernet-encrypted ciphertext per provider |
| Env | `MCPFARM_SECRETS_KEY` — never in repo |

### 8.3 Settings.jsx changes

- Save triggers `PUT /llm-keys/{provider}` instead of `localStorage.setItem` for secret values.
- Load triggers `GET /llm-keys` on mount; populate fields with masked values.
- Empty field on save = no change (do not overwrite with blank).
- Chat page and per-server Chat tab never read raw keys; both call `/chat/completions` only.

### 8.4 Supported providers (unchanged)

| Provider ID | Settings label |
|-------------|----------------|
| `claude` | Claude API Key |
| `openai` | OpenAI API Key |
| `ollama` | Ollama URL (not encrypted; URL only) |
| `bedrock` | Bedrock API Key + Region + Models |
| `azure` | Azure OpenAI Key + Endpoint + Deployments |
| `openrouter` | OpenRouter API Key + Models |
| `grok` | Grok API Key + Models |
| `gemini` | Gemini API Key + Models |

---

## 9. Implementation phases

### Phase 1 — Chat shell + shared primitives (no vectors)

- [ ] Add Chat nav + `ChatMode.jsx`
- [ ] Install assistant-ui; add Thread + ThreadList
- [ ] Build shared `ChatThread`, `ComposerToolbar`, `useMcpChatRuntime`, `chatOrchestrator.js`
- [ ] `LocalRuntime` + static binding only (manual server select, all tools)
- [ ] Claude provider via existing `/claude` proxy
- [ ] Generic MCP Tool UI
- [ ] localStorage thread list

**Exit:** Usable chat with manual server selection.

### Phase 2 — Multi-LLM + encrypted keys

- [ ] `secrets_vault.py` + `/llm-keys` + `/chat/completions`
- [ ] Migrate Settings to server-side keys
- [ ] Wire all `LLM_PROVIDERS` through chat orchestrator
- [ ] Provider/model picker in composer

**Exit:** Chat works with any configured provider; keys encrypted.

### Phase 2b — Reimplement per-server Chat tab

- [ ] Rewrite `ChatTab.jsx` on `useMcpChatRuntime` + `ChatThread` with fixed single-server binding
- [ ] Add `toStaticBinding()` helper to `toolBinding.js`
- [ ] Keep tool discovery + `onLoadTools` + sample prompts + running/stopped gating
- [ ] Remove old `ChatMessage` and manual tool loop
- [ ] Verify no regression to other `ServerDetail` tabs

**Exit:** Per-server Chat tab runs on assistant-ui with streaming; parity checklist (§7.5) passes.

### Phase 3 — Redis vector index

- [ ] Connect auth-gateway to hd-redis
- [ ] `vector_index.py` + `vector_indexer.py`
- [ ] Index all server metadata + READMEs on reindex
- [ ] `POST /vectors/search`
- [ ] Dynamic binding in `toolBinding.js`
- [ ] AutoSelectionChips UI

**Exit:** Auto mode selects relevant tools.

### Phase 4 — Static tool picker + lifecycle

- [ ] `ToolPickerDrawer` with per-tool checkboxes
- [ ] Pin-to-thread for static selection
- [ ] Index tools on server start/stop hooks
- [ ] `POST /admin/vectors/reindex` + stats endpoint

**Exit:** Full v1 acceptance criteria met.

### Phase 5 — Polish (v1.1)

- [ ] @mention server boost
- [ ] Hybrid auto + manual override
- [ ] Server-side thread persistence
- [ ] Per-tool rich Tool UI for top 20 tools

---

## 10. Testing plan

### 10.1 Unit tests

| Area | Cases |
|------|-------|
| `toolBinding.resolveStatic` | Server-only, tool-only, empty, pin |
| `toolBinding.resolveDynamic` | Mock Redis responses, truncation, min_score |
| `toolBinding.toStaticBinding` | Single-server shape, anthropicName mapping |
| `vector_indexer` | README chunking, tool doc format |
| `secrets_vault` | Encrypt roundtrip, wrong key fails |

### 10.2 Integration tests

| Scenario | Expected |
|----------|----------|
| Auto: "nmap scan 10.0.0.1" | Binds nmap-mcp when running |
| Auto: no running servers | Clear error, no LLM call |
| Manual: select nmap-mcp only | Only nmap tools in context |
| Manual: pin + second message | Same binding without re-select |
| Tool call execution | `mcpClient.callTool` invoked with correct args |
| Redis down | Fallback keyword or graceful error |
| Key vault | Chat works without localStorage keys |
| Per-server tab: bound to current server | Only that server's tools in context; no vector call |
| Per-server tab: stopped server | Composer disabled; discovery blocked |
| Per-server tab: discover then chat | `onLoadTools` fires; binding uses discovered tools |

### 10.3 Manual QA checklist

- [ ] Chat nav position correct
- [ ] Dark/light theme consistent
- [ ] Streaming cancel mid-generation
- [ ] Edit message + regenerate
- [ ] Long tool result renders without layout break
- [ ] 25+ tool binding truncates with warning chip
- [ ] Per-server Chat tab matches parity checklist (§7.5)
- [ ] Switching between `ServerDetail` tabs does not leak or duplicate threads

---

## 11. Open questions

| # | Question | Recommendation |
|---|----------|----------------|
| 1 | hd-redis network: shared compose or host port? | Add external network `hd-redis_default` to auth-gateway service |
| 2 | Default binding mode for new users? | Auto |
| 3 | Max agentic loop iterations? | 10 (match `claude.js`) |
| 4 | Store tool schemas in Redis or fetch live? | Redis for search/ranking; live `tools/list` for execution schema |
| 5 | Deprecate Prompt mode long-term? | No; keep for power users |
| 6 | Embedding model without OpenAI key? | Require Ollama embed model on farm host |
| 7 | Persist per-server tab threads across visits? | No in v1 (ephemeral); optional `chatThreads.js` keyed by `serverName` in v1.1 |
| 8 | Keep the explicit "Discover Tools" button in the tab? | Yes — preserves current UX and lets binding refresh on demand |

---

## Appendix A: Environment variables

| Variable | Service | Description |
|----------|---------|-------------|
| `REDIS_URL` | auth-gateway | `redis://hd-redis:6379` |
| `MCPFARM_VECTOR_PREFIX` | auth-gateway | `mcpfarm:v1` |
| `MCPFARM_SECRETS_KEY` | auth-gateway | Fernet key for LLM secrets |
| `OPENAI_API_KEY` | auth-gateway | Embeddings + OpenAI chat |
| `OLLAMA_URL` | auth-gateway | Fallback embeddings |
| `VECTOR_DIM` | auth-gateway | `1536` |
| `VECTOR_MIN_SCORE` | auth-gateway | `0.72` |
| `VECTOR_TOP_K_SERVERS` | auth-gateway | `5` |
| `VECTOR_TOP_K_TOOLS` | auth-gateway | `20` |

## Appendix B: Comparison with existing modes

| Feature | Chat (new) | Prompt | Nova | ChatTab (reimplemented) |
|---------|------------|--------|------|-------------------------|
| UI framework | assistant-ui | Custom | Custom | **assistant-ui** |
| Multi-LLM | Yes | No | No | Yes |
| Cross-server tools | Yes | Yes | Yes | No (single server) |
| Dynamic binding | Yes | No | No | No |
| Static tool-level binding | Yes | Server only | No | Fixed to current server |
| Vector search | Yes | No | No | No |
| Streaming / cancel / edit | Yes | Partial | Partial | **Yes (new)** |
| Shared orchestrator | Yes | No | No | Yes (`chatOrchestrator`) |
| Avatar | No | No | Yes | No |

## Appendix C: References

- [assistant-ui Installation](https://www.assistant-ui.com/docs/installation.md)
- [assistant-ui LocalRuntime](https://www.assistant-ui.com/docs/runtimes/custom/local-runtime.md)
- [assistant-ui Tool UI](https://www.assistant-ui.com/docs/tools/tool-ui.md)
- [Redis vector search](https://redis.io/docs/latest/develop/ai/search-and-query/vectors/)
- Existing code: `mcpfarm-ui/src/lib/claude.js`, `mcpfarm-ui/src/lib/llm.js`, `mcpfarm-ui/src/lib/mcp.js`
- Per-server tab being reimplemented: `mcpfarm-ui/src/components/ChatTab.jsx` (rendered by `ServerDetail.jsx` ~line 756)
