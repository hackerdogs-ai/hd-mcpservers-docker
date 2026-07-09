# n8n Nodes for MCP Farm Tools — PRD, Technical Spec & Implementation Design

**Version:** 1.0  
**Date:** 2026-07-09  
**Status:** Draft  
**Audience:** Hackerdogs engineering, platform, and partner teams  
**Related docs:** [FARM-ARCHITECTURE.md](./FARM-ARCHITECTURE.md), [FARM-PRD.md](./FARM-PRD.md), [mcpfarm-ui/src/lib/mcp.js](../mcpfarm-ui/src/lib/mcp.js)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Product Requirements (PRD)](#3-product-requirements-prd)
4. [Technical Specification](#4-technical-specification)
5. [Approach Options](#5-approach-options)
6. [Recommended Architecture](#6-recommended-architecture)
7. [Implementation Design](#7-implementation-design)
8. [Publishing: Private Catalog](#8-publishing-private-catalog)
9. [Publishing: Public Catalog](#9-publishing-public-catalog)
10. [Step-by-Step Implementation Plan](#10-step-by-step-implementation-plan)
11. [Effort Estimates](#11-effort-estimates)
12. [Risks, Constraints & Open Questions](#12-risks-constraints--open-questions)
13. [References](#13-references)

---

## 1. Executive Summary

Hackerdogs maintains **400+ MCP server packages** in this repository, each exposing one or more tools via FastMCP over Docker. n8n users expect first-class workflow nodes — typed parameters, credentials, and discoverability in the node palette — not raw JSON-RPC calls.

**Recommended approach:** Build thin **n8n node wrappers** that call existing **MCP Farm gateway endpoints**. Each node performs HTTP MCP session management and `tools/call` against `/{server-name}/mcp`, reusing the same protocol already implemented in `mcpfarm-ui/src/lib/mcp.js`. Execution stays in MCP Farm containers; n8n nodes are typed HTTP frontends only.

This avoids rewriting 400+ Python integrations in TypeScript, satisfies n8n verified-node technical constraints (no subprocess, no filesystem, no runtime npm deps), and scales via **code generation** from `@mcp.tool()` definitions in each `mcp_server.py`.

| Distribution channel | Fit | Notes |
|---------------------|-----|-------|
| **Private npm catalog** | Excellent | Primary target; security/CLI tools allowed |
| **Public verified catalog** | Selective | API-only tools; pentest scanners likely rejected |
| **Generic MCP Client (no custom nodes)** | Fast MVP | No typed UI; acceptable for internal pilots |

---

## 2. Problem Statement

### Current state

- MCP servers are consumed by Claude, Cursor, Hackerdogs Chat, and other MCP clients via streamable HTTP or stdio.
- MCP Farm exposes a unified entry point: `https://mcp.hackerdogs.ai/{server-name}/mcp/` (local: `http://localhost:8485/{server-name}/mcp`).
- n8n has native MCP support (MCP Client, MCP Client Tool nodes since v1.88) but provides a **generic** interface — users pick tools from a dynamic list and pass JSON arguments.

### Gap

n8n workflow authors want:

- Named nodes (`Gitleaks`, `Naabu`, `Nuclei`) in the palette
- Typed form fields mapped to tool parameters
- Reusable credentials (Farm URL + API key)
- Optional catalog distribution (private registry for enterprise customers; public npm for API integrations)

### What we will not do

- Reimplement tool logic in TypeScript (duplicate of Python MCP servers)
- Run CLI binaries inside n8n node code (blocked by n8n verified-node rules and n8n v2.0 security defaults)
- Build a custom “catalog UI” inside n8n (n8n distributes nodes via npm, not a browsable app store)

---

## 3. Product Requirements (PRD)

### 3.1 Goals

| ID | Goal | Success criteria |
|----|------|------------------|
| G1 | Expose MCP Farm tools as n8n workflow nodes | User can drag `Gitleaks` node, set `source_url`, run workflow |
| G2 | Reuse existing MCP infrastructure | Zero changes to MCP server containers for MVP |
| G3 | Scale to full tool library | Codegen produces nodes for all `@mcp.tool()` definitions |
| G4 | Single credential type | User configures Farm URL + API key once |
| G5 | Private catalog for enterprise | Packages install from private npm via n8n Community Nodes UI |
| G6 | Public catalog for eligible API tools | Verified nodes discoverable in n8n node panel (subset only) |

### 3.2 Non-goals (v1)

- Replacing MCP Farm gateway or changing auth model
- Supporting stdio transport from n8n (Farm HTTP only)
- Per-tool billing or n8n marketplace monetization (n8n has no paid node marketplace)
- n8n Cloud approval for offensive security / pentest scanner nodes
- Real-time hot-reload of nodes without n8n container restart

### 3.3 User personas

| Persona | Need |
|---------|------|
| **Security engineer** | Chain gitleaks → notify → ticket in n8n without writing MCP JSON-RPC |
| **Enterprise customer** | Install `@hackerdogs/n8n-nodes-*` from private registry; no public npm |
| **Integration partner** | Publish verified node for their API tool (e.g. N2YO) to public catalog |
| **Platform operator** | Regenerate nodes when `mcp_server.py` tools change; CI publishes semver packages |

### 3.4 User stories

1. **As a workflow author**, I configure `MCP Farm API` credentials once and use any Hackerdogs node.
2. **As a workflow author**, I see tool-specific parameters (not raw JSON) when configuring a node operation.
3. **As an admin**, I pre-install a fixed set of community packages via `N8N_COMMUNITY_PACKAGES` env var.
4. **As a maintainer**, I run `make n8n-nodes-generate` after changing `@mcp.tool()` signatures and CI publishes updated packages.

### 3.5 Functional requirements

| ID | Requirement |
|----|-------------|
| FR1 | Each node package integrates exactly one MCP server (one Docker image / server name) |
| FR2 | Each `@mcp.tool()` maps to one n8n operation (or resource/action pair) |
| FR3 | Node executes MCP Streamable HTTP session: `initialize` → `notifications/initialized` → `tools/call` |
| FR4 | Node handles session expiry (HTTP 404 + `mcp-session-id` → re-initialize and retry once) |
| FR5 | Node maps MCP tool result `content[]` to n8n output items (`[{ json: ... }]`) |
| FR6 | Credentials store: `baseUrl`, `apiKey` (Bearer token); optional `serverName` override |
| FR7 | Errors from Farm (401, 403, 502, MCP JSON-RPC error) surface as `NodeOperationError` with actionable messages |
| FR8 | Code generator reads Python tool metadata from `mcp_server.py` (AST or regex) |

### 3.6 Non-functional requirements

| ID | Requirement |
|----|-------------|
| NFR1 | Node code uses `this.helpers.httpRequest` only — **zero runtime npm dependencies** (verified catalog compliance) |
| NFR2 | MIT license for public packages |
| NFR3 | TypeScript, `@n8n/node-cli` scaffolding, passes `n8n-node lint` |
| NFR4 | Publish via GitHub Actions with npm provenance (required for verified nodes since 2026-05-01) |
| NFR5 | P95 node execution overhead (HTTP/session, excluding tool runtime) < 2s |

---

## 4. Technical Specification

### 4.1 System context

```
┌─────────────────┐         HTTPS + Bearer          ┌──────────────────────────┐
│  n8n Workflow   │ ──────────────────────────────▶ │  MCP Farm Gateway        │
│  (n8n node)     │   POST /{server}/mcp            │  Caddy → auth-gateway    │
└─────────────────┘                                 └────────────┬─────────────┘
                                                                 │
                                                                 ▼
                                                    ┌──────────────────────────┐
                                                    │  MCP Server Container    │
                                                    │  (e.g. gitleaks-mcp)     │
                                                    │  FastMCP streamable-http │
                                                    └──────────────────────────┘
```

The n8n node is **not** in the execution path for CLI/subprocess logic. It is an MCP client over HTTP, identical in role to `mcpfarm-ui`.

### 4.2 MCP Farm endpoint contract

| Item | Value |
|------|-------|
| Production base URL | `https://mcp.hackerdogs.ai` |
| Local dev base URL | `http://localhost:8485` (default `FARM_PORT`) |
| Per-server MCP path | `/{server-name}/mcp` |
| Auth header | `Authorization: Bearer <farm-api-key>` |
| Content-Type | `application/json` |
| Accept | `application/json, text/event-stream` |
| Session header | `mcp-session-id: <uuid>` (after initialize) |

**Example — tool call via Farm (from FARM-ARCHITECTURE.md):**

```http
POST https://mcp.hackerdogs.ai/naabu-mcp/mcp
Authorization: Bearer hd_sk_a1b2c3d4...
Content-Type: application/json

{"jsonrpc":"2.0","id":1,"method":"tools/call",
 "params":{"name":"run_naabu","arguments":{"arguments":"-host 10.0.0.1"}}}
```

### 4.3 MCP session lifecycle (normative)

Reference implementation: `mcpfarm-ui/src/lib/mcp.js`.

| Step | Method | Body | Notes |
|------|--------|------|-------|
| 1. Initialize | `POST /{server}/mcp` | `{"jsonrpc":"2.0","id":1,"method":"initialize","params":{...}}` | No session header |
| 2. Capture session | — | — | Read `mcp-session-id` response header |
| 3. Initialized notification | `POST /{server}/mcp` | `{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}` | Include session header |
| 4. List tools (optional) | `POST` | `{"method":"tools/list",...}` | Used by generic node / validation |
| 5. Call tool | `POST` | `{"method":"tools/call","params":{"name":"...","arguments":{...}}}` | Primary execution |
| 6. Terminate (optional) | `DELETE /{server}/mcp` | — | Spec SHOULD; clear cached session |

**Initialize params (match UI client):**

```json
{
  "protocolVersion": "2024-11-05",
  "capabilities": { "tools": {} },
  "clientInfo": { "name": "n8n-nodes-hackerdogs", "version": "1.0.0" }
}
```

**Session recovery:** On HTTP 404 when `mcp-session-id` was sent, clear session, re-run steps 1–3, retry request once (MCP Streamable HTTP spec §Session Management).

**Response parsing:** Responses may be SSE (`data: {...}` lines) or plain JSON. Parser must handle both (see `parseSseResponse` in `mcp.js`).

### 4.4 Auth and authorization (Farm-side)

Before a request reaches an MCP container, auth-gateway verifies (see FARM-ARCHITECTURE §7):

- Bearer token exists and is active
- Token not expired
- Token scopes include `{server-name}` or `*`
- Rate limit not exceeded

n8n nodes **do not** implement this logic — they pass the Bearer token; Farm returns 401/403 on failure.

### 4.5 Tool metadata source of truth

| Source | Location | Used for |
|--------|----------|----------|
| Python tool definitions | `{tool}-mcp/mcp_server.py` | Codegen: operation names, parameters, descriptions |
| Server name | Directory name (e.g. `gitleaks-mcp`) | URL path segment |
| Docker image | `hackerdogs/{tool}-mcp:latest` | Documentation only (not called from n8n) |
| Generic CLI template | `phase2-common/mcp_server_generic.py` | Most servers expose `run(arguments, timeout_seconds)` |

**Example — multi-operation server (gitleaks-mcp):**

| MCP tool name | n8n operation | Parameters |
|---------------|---------------|------------|
| `run_gitleaks` | Run Scan | `source_url`, `arguments`, `timeout_seconds` |
| `download_file` | Download File | `url`, `extract` |
| `cleanup_downloads` | Cleanup Downloads | `job_id` |

### 4.6 n8n node output mapping

MCP `tools/call` result shape (typical):

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [{ "type": "text", "text": "..." }],
    "isError": false
  }
}
```

Node maps to n8n items:

```typescript
return [{
  json: {
    result: parsedTextOrJson,
    isError: result.isError ?? false,
    toolName: 'run_gitleaks',
    serverName: 'gitleaks-mcp',
  },
}];
```

If `isError: true` or JSON-RPC `error` present, throw `NodeOperationError`.

### 4.7 Credentials schema

**Credential type:** `mcpFarmApi`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `baseUrl` | string | Yes | Farm gateway URL, no trailing slash |
| `apiKey` | string | Yes | Farm Bearer token (`hd_sk_...`) |

All per-server node packages share this credential type from a common base package or duplicated generated credential file.

---

## 5. Approach Options

### Option A — One npm package per MCP server (recommended)

| Aspect | Detail |
|--------|--------|
| Package naming | `n8n-nodes-gitleaks` or `@hackerdogs/n8n-nodes-gitleaks` |
| Node count | 1 node per package, N operations per `@mcp.tool()` |
| UX | Best — named nodes, typed fields per tool |
| Catalog | Each package listed separately in Community Nodes |
| Verification | One Creator Portal submission per package |
| Maintenance | Codegen + shared client library |
| Effort | ~400 packages, but generated; CI matrix publish |

**When to choose:** Production private catalog, partner-facing integrations, best workflow author experience.

---

### Option B — Monorepo, single scoped package with many nodes

| Aspect | Detail |
|--------|--------|
| Package naming | `@hackerdogs/n8n-nodes-farm` |
| Node count | 400+ node types in one package |
| UX | Good palette coverage, one install |
| Catalog | Single Community Nodes install |
| Verification | **Likely rejected** — n8n requires one third-party service per verified package |
| Maintenance | One semver bumps all nodes |
| Effort | Lower npm overhead; larger package size |

**When to choose:** Internal/private use only; fastest “install everything” experience.

---

### Option C — One generic “MCP Farm Tool” node

| Aspect | Detail |
|--------|--------|
| Package naming | `@hackerdogs/n8n-nodes-mcp-farm` |
| Parameters | `serverName`, `toolName`, `arguments` (JSON) |
| UX | Poor — users must know tool names and JSON schemas |
| Catalog | Single package |
| Effort | ~1–2 weeks total |

**When to choose:** MVP / pilot before codegen investment; internal power users.

---

### Option D — No custom nodes; use n8n built-in MCP Client

| Aspect | Detail |
|--------|--------|
| Components | n8n MCP Client or MCP Client Tool + Farm HTTP URL |
| Config | `N8N_COMMUNITY_PACKAGES_ALLOW_TOOL_USAGE=true` if using community MCP client |
| UX | Generic; AI Agent workflows only for Client Tool |
| Effort | Days |

**When to choose:** Immediate validation that Farm works with n8n; not a catalog product.

---

### Option comparison matrix

| Criterion | A: Per-server | B: Monorepo | C: Generic | D: Built-in MCP |
|-----------|---------------|-------------|------------|-----------------|
| Typed parameters | ✅ | ✅ | ❌ | ❌ |
| Named palette entries | ✅ | ✅ | ❌ | ❌ |
| Verified catalog fit | ✅ | ❌ | ⚠️ | N/A |
| Private catalog fit | ✅ | ✅ | ✅ | N/A |
| Codegen required | Yes | Yes | No | No |
| Install granularity | Per tool | All-at-once | Single | n8n built-in |
| Maintenance at 400+ tools | Medium | Low | Low | None |

**Recommendation:** **Option A** for product catalog; **Option C** as Phase 0 spike; **Option D** for same-day integration test.

---

## 6. Recommended Architecture

### 6.1 Repository layout (new)

```
n8n-nodes/
├── packages/
│   ├── mcp-farm-client/          # Shared TypeScript MCP HTTP client
│   │   ├── src/
│   │   │   ├── McpFarmClient.ts
│   │   │   ├── parseSseResponse.ts
│   │   │   └── types.ts
│   │   └── package.json          # Dev dependency only; inlined or bundled at build
│   │
│   └── credentials/
│       └── McpFarmApi.credentials.ts
│
├── templates/
│   ├── node.programmatic.ts.ejs  # Handlebars/ejs template for generated node
│   ├── package.json.ejs
│   └── README.md.ejs
│
├── generated/                    # Gitignored or committed — policy TBD
│   ├── n8n-nodes-gitleaks/
│   ├── n8n-nodes-naabu/
│   └── ...
│
├── scripts/
│   ├── generate-nodes.ts         # Scan *-mcp/mcp_server.py → emit packages
│   ├── parse-python-tools.ts     # AST: @mcp.tool defs, docstrings, type hints
│   └── publish-matrix.yml        # CI helper
│
├── package.json                  # npm workspaces root
└── README.md
```

### 6.2 Code generation pipeline

```
*-mcp/mcp_server.py
        │
        ▼
  parse-python-tools.ts
   (AST: @mcp.tool functions,
    docstring Args: sections,
    type hints → n8n property types)
        │
        ▼
  templates/*.ejs
        │
        ▼
  generated/n8n-nodes-{name}/
   ├── nodes/Gitleaks/Gitleaks.node.ts
   ├── credentials/McpFarmApi.credentials.ts
   ├── package.json
   └── README.md
        │
        ▼
  npm run build && n8n-node lint
        │
        ▼
  publish → npm (public or private registry)
```

**Python → n8n type mapping:**

| Python hint | n8n property type |
|-------------|-------------------|
| `str` | `string` |
| `int` | `number` |
| `float` | `number` |
| `bool` | `boolean` |
| `str = ""` | `string`, optional |
| No hint | `string` (safe default) |

**Server name derivation:** `gitleaks-mcp` directory → package `n8n-nodes-gitleaks`, Farm path `gitleaks-mcp`, default server name `gitleaks-mcp`.

### 6.3 Shared MCP Farm client (design)

Port of `mcpfarm-ui/src/lib/mcp.js` to TypeScript using n8n's `IHttpRequestOptions`:

```typescript
class McpFarmClient {
  constructor(
    private baseUrl: string,
    private apiKey: string,
    private httpRequest: (options: IHttpRequestOptions) => Promise<any>,
  ) {}

  async initialize(serverName: string): Promise<void>;
  async callTool(serverName: string, toolName: string, args: Record<string, unknown>): Promise<McpToolResult>;
  async listTools(serverName: string): Promise<McpToolDefinition[]>;
  resetSession(serverName: string): void;
}
```

**Design decisions:**

- **Fresh session per n8n execution** (v1): Simple, stateless; no cross-execution session cache.
- **No runtime deps:** Client code compiled into each node package (tree-shaken) or duplicated via codegen inline — final published package must have `"dependencies": {}`.
- **Timeout:** Configurable per operation; default 600s for long scans (n8n workflow timeout must align).

### 6.4 Generated node template (design)

Each generated node:

- Extends `INodeType`
- Declares `credentials: ['mcpFarmApi']`
- Declares `properties` per operation (n8n `displayOptions` keyed on `operation`)
- `execute()` reads operation → calls `McpFarmClient.callTool(serverName, toolName, args)`

**Display name:** Humanized from server name (`gitleaks-mcp` → `Gitleaks`).

**Subtitle / description:** From FastMCP server instructions or first line of README.

---

## 7. Implementation Design

### 7.1 Phase 0 — Spike (Option C or D)

**Objective:** Prove Farm ↔ n8n connectivity.

**Steps:**

1. Deploy MCP Farm locally (`FARM_PORT=8485`) with one server (e.g. `n2yo-mcp`).
2. In n8n (Docker), add workflow with **MCP Client** node:
   - URL: `http://host.docker.internal:8485/n2yo-mcp/mcp`
   - Auth: Bearer credential with Farm API key
3. Execute `tools/list` and `tools/call` for `n2yo_info`.
4. Document network requirements (n8n container must reach Farm host).

**Exit criteria:** Successful tool call from n8n to Farm.

---

### 7.2 Phase 1 — Reference node (manual, Option A)

**Objective:** One hand-written package as codegen reference.

**Target:** `n2yo-mcp` (single tool, no CLI) or `gitleaks-mcp` (multi-tool, representative).

**Steps:**

1. Scaffold: `npm create @n8n/node@latest` → programmatic template.
2. Implement `McpFarmApi.credentials.ts`.
3. Implement `McpFarmClient` with `httpRequest` injection.
4. Implement node operations matching all `@mcp.tool()` names.
5. Test: `n8n-node dev` against local Farm.
6. Run `n8n-node lint` and `npx @n8n/scan-community-package n8n-nodes-{name}`.
7. Private publish to Verdaccio or `npm link` into n8n custom folder.

**Exit criteria:** Reference package passes lint; workflow runs end-to-end.

---

### 7.3 Phase 2 — Code generator

**Objective:** Automate node creation for all MCP servers.

**Steps:**

1. Implement `parse-python-tools.ts`:
   - Walk repo for `*-mcp/mcp_server.py`
   - Parse `@mcp.tool()` decorated functions (Python `ast` via subprocess or regex fallback)
   - Extract function name, docstring, parameters from signature + `Args:` section
2. Implement `generate-nodes.ts`:
   - Emit package per server into `n8n-nodes/generated/`
   - Skip servers with zero tools
3. Add root `Makefile` target: `make n8n-nodes-generate`
4. Diff review in CI; fail if generated output stale

**Edge cases:**

| Case | Handling |
|------|----------|
| Generic `run()` only | Single operation `Run` with `arguments` string + `timeout_seconds` |
| Async tools | Generated `execute` is `async` |
| Complex nested args | v1: JSON string field; v2: structured properties |
| acuvity-mcp-server-* prefix | Normalize server name from directory |

**Exit criteria:** Generator emits valid packages for ≥10 diverse servers; CI validates build.

---

### 7.4 Phase 3 — CI/CD publish pipeline

**Objective:** Reproducible publish to private (and optionally public) npm.

**GitHub Actions workflow (`publish.yml`):**

1. Trigger: tag push `n8n-nodes-v*` or per-package tags
2. Setup Node 20+, `@n8n/node-cli` ≥ 0.23.0
3. `npm run generate` (ensure up to date)
4. Matrix: build each changed package
5. `npm publish --provenance --access public|restricted`
6. npm Trusted Publisher (OIDC) — no long-lived `NPM_TOKEN` required

**Versioning:**

- Per-package semver in `generated/n8n-nodes-*/package.json`
- Bump minor when tools added; patch for fixes; major for breaking parameter changes

---

### 7.5 Phase 4 — n8n instance integration

**Objective:** Operators install and manage Hackerdogs nodes.

**Self-hosted Docker (private registry):**

```yaml
environment:
  N8N_COMMUNITY_PACKAGES_REGISTRY: https://npm.yourcompany.com
  N8N_COMMUNITY_PACKAGES_AUTH_TOKEN: ${NPM_AUTH_TOKEN}
  N8N_COMMUNITY_PACKAGES_MANAGED_BY_ENV: "true"
  N8N_COMMUNITY_PACKAGES: |
    [
      {"name": "@hackerdogs/n8n-nodes-gitleaks", "version": "1.0.0"},
      {"name": "@hackerdogs/n8n-nodes-naabu", "version": "1.0.0"}
    ]
```

**Alternative — custom Docker image (no registry UI):**

1. `npm run build` all packages
2. COPY `dist/` to `/home/node/.n8n/custom/` in custom n8n image
3. Set `N8N_CUSTOM_EXTENSIONS=/home/node/.n8n/custom`
4. Restart n8n on updates (no hot-plug)

---

## 8. Publishing: Private Catalog

### 8.1 What “private catalog” means in n8n

n8n has **no custom catalog browser**. Private distribution means:

1. Packages published to a **private npm registry** (Verdaccio, GitHub Packages, Artifactory, AWS CodeArtifact)
2. n8n configured to pull from that registry
3. Users install via **Settings → Community Nodes** (or env-managed install)

### 8.2 Requirements

| Item | Detail |
|------|--------|
| n8n license | **Enterprise** required for `N8N_COMMUNITY_PACKAGES_REGISTRY` ≠ npmjs.org |
| Registry | Host private `@hackerdogs` scope |
| Auth | `N8N_COMMUNITY_PACKAGES_AUTH_TOKEN` |
| Package naming | `@hackerdogs/n8n-nodes-{tool}` recommended |
| Keyword | `n8n-community-node-package` in each `package.json` |

### 8.3 Private publish checklist (per package)

- [ ] `"dependencies": {}` in published package
- [ ] `n8n.nodes` array points to compiled `.node.js` files
- [ ] README with Farm credential setup and example workflow
- [ ] Scoped publish: `npm publish --access restricted`
- [ ] Internal doc listing available packages (substitute for catalog UI)

### 8.4 Operator runbook

1. Provision Verdaccio (or use GitHub Packages).
2. Configure n8n env vars (see §7.5).
3. Create Farm API key with scopes for required servers (or `*`).
4. Install packages via UI or `N8N_COMMUNITY_PACKAGES`.
5. Create credential `MCP Farm API` in n8n with base URL and key.
6. Build workflows using Hackerdogs nodes.

---

## 9. Publishing: Public Catalog

### 9.1 What “public catalog” means in n8n

- Packages on **public npm** (`n8n-nodes-*` or `@scope/n8n-nodes-*`)
- **Verified** nodes: reviewed by n8n, discoverable in node panel, available on n8n Cloud
- **Unverified** nodes: install by name if `N8N_UNVERIFIED_PACKAGES_ENABLED=true`

### 9.2 Verified node requirements (2026)

| Requirement | Hackerdogs wrapper compliance |
|-------------|------------------------------|
| Scaffold via `@n8n/node` CLI | ✅ Planned |
| MIT license, public GitHub repo | ✅ Required for public |
| No runtime npm dependencies | ✅ HTTP-only client |
| No env var / filesystem access in node code | ✅ Farm handles execution |
| One third-party service per package | ✅ One MCP server per package |
| GitHub Actions publish + npm provenance | ✅ Required since 2026-05-01 |
| Pass `@n8n/scan-community-package` | ✅ Must verify per package |
| English UI and docs | ✅ Required |

### 9.3 Policy expectations (likely rejection)

These categories are **poor candidates** for n8n Cloud verified catalog even with compliant code:

- Port scanners (naabu, nmap, masscan)
- Exploitation frameworks (metasploit, sqlmap)
- Credential attacks (hydra, hashcat)
- Secret scanners that clone arbitrary repos (gitleaks) — abuse risk

**Good candidates** for public verified submission:

- API integrations: N2YO, Shodan (API), financial data, weather, search APIs
- Passive OSINT with clear API terms
- DevOps/API tools without offensive capability

### 9.4 Public publish checklist (per package)

- [ ] Public GitHub repo matching npm `repository` field
- [ ] npm Trusted Publisher configured for `publish.yml`
- [ ] `@n8n/node-cli` ≥ 0.23.0
- [ ] `npx @n8n/scan-community-package` → 0 violations
- [ ] README with screenshots, example workflow, credential setup
- [ ] Submit at [creators.n8n.io/nodes](https://creators.n8n.io/nodes)
- [ ] Respond to n8n review feedback (typical 1–4 weeks)

### 9.5 Important constraints

- **No paid nodes** — n8n has no revenue share or paid marketplace for community nodes.
- **Code is public** on npm — acceptable for open integrations; not for proprietary logic (wrapper is thin anyway).
- **n8n may reject** nodes competing with enterprise features.

---

## 10. Step-by-Step Implementation Plan

### Milestone timeline

| Milestone | Duration | Deliverable |
|-----------|----------|-------------|
| M0: Connectivity spike | 2–3 days | Doc: n8n ↔ Farm working via MCP Client |
| M1: Reference package | 1–2 weeks | `n8n-nodes-n2yo` or `n8n-nodes-gitleaks` on private registry |
| M2: Code generator v1 | 1–2 weeks | Generate packages for all `*-mcp` servers |
| M3: CI publish | 1 week | GitHub Actions → private npm with provenance |
| M4: Pilot catalog (20 tools) | 2 weeks | Top 20 servers published, internal docs |
| M5: Full private catalog | 2–4 weeks | All generated packages published |
| M6: Public verified (subset) | Ongoing | Cherry-picked API tools submitted to Creator Portal |

### Detailed steps — M1 reference package

1. Create `n8n-nodes/` directory at repo root.
2. Run `npm create @n8n/node@latest` inside `n8n-nodes/packages/n8n-nodes-n2yo`.
3. Add `McpFarmClient.ts` (copy logic from `mcpfarm-ui/src/lib/mcp.js`).
4. Replace default operations with `n2yo_info` operation.
5. Add credential type `mcpFarmApi`.
6. Configure `n8n-node dev` to point at local n8n with Farm on `localhost:8485`.
7. Run tests manually in n8n UI.
8. Run `npm run lint && npm run build`.
9. Publish to private registry v0.1.0.

### Detailed steps — M2 code generator

1. Inventory: `find . -maxdepth 1 -name '*-mcp' -type d | wc -l` (~401 directories).
2. For each directory, locate `mcp_server.py`.
3. Parse tools; write JSON manifest `n8n-nodes/tool-manifest.json`.
4. Render templates → `generated/n8n-nodes-{slug}/`.
5. Run workspace build: `npm run build --workspaces`.
6. Spot-check 5 servers: generic CLI, multi-tool, API-only, acuvity-prefixed, minimal stub.
7. Add CI job: `make n8n-nodes-generate && git diff --exit-code`.

### Detailed steps — M3 CI publish

1. Copy `publish.yml` from [n8n-nodes-starter](https://github.com/n8n-io/n8n-nodes-starter).
2. Configure npm Trusted Publisher on GitHub org.
3. Add workflow dispatch for single-package publish (avoid matrix 401 jobs on every commit).
4. Tag-driven full catalog release (`n8n-nodes-catalog-2026.07`).

### Detailed steps — Operator: install in n8n

1. Set `N8N_COMMUNITY_PACKAGES_REGISTRY` and auth token.
2. Install `@hackerdogs/n8n-nodes-gitleaks` from Community Nodes UI.
3. Restart n8n if nodes do not appear (required for custom/private nodes).
4. Create credential: base URL + API key.
5. Add node to workflow; select operation; execute.

---

## 11. Effort Estimates

| Work item | Engineer-weeks | Notes |
|-----------|----------------|-------|
| M0 spike | 0.5 | Option D |
| M1 reference node + client | 1–2 | Foundation |
| M2 codegen | 1–2 | Highest leverage |
| M3 CI/CD | 1 | Reusable |
| M4 pilot (20 tools) | 1 | QA + docs |
| M5 full catalog (401 servers) | 2–4 | Mostly automated; QA sampling |
| M6 public verified (20 API tools) | 4–8 | Review cycles dominate |
| **Total (private catalog)** | **6–10 weeks** | 1–2 engineers |
| **Total (public verified subset)** | **+1–3 months** | Policy-dependent |

Compare to **native rewrite** (no Farm wrapper): estimated **2–4+ person-years** for 401 servers.

---

## 12. Risks, Constraints & Open Questions

### 12.1 Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| n8n rejects security tools for verified catalog | Public catalog smaller than hoped | Target private catalog; document policy |
| Long-running scans exceed n8n execution timeout | Workflow failures | Document timeout settings; async pattern later |
| Session handling edge cases (502, stale session) | Intermittent errors | Port retry logic from `mcp.js`; integration tests |
| 401 packages × CI matrix cost | Slow/noisy CI | Publish changed packages only; tag releases |
| n8n v2.0 security defaults | Execute Command unavailable | Farm wrapper avoids this entirely |
| Generator misses dynamic Python tools | Incomplete nodes | Manifest override file for manual fixes |
| Enterprise license required for private registry | Cost | Budget approval; or custom Docker image path |

### 12.2 Constraints

- n8n node reload requires **container restart** (no hot-plug).
- MCP Farm must be **network-reachable** from n8n (Docker networking config).
- Verified nodes: **`dependencies: {}`** — shared client must be bundled, not npm-linked at runtime.
- One service per verified package — no monorepo mega-package for public catalog.

### 12.3 Open questions

| # | Question | Owner | Decision deadline |
|---|----------|-------|-------------------|
| OQ1 | Commit `generated/` to repo or build in CI only? | Platform | Before M2 |
| OQ2 | Scoped `@hackerdogs` vs unscoped `n8n-nodes-*` naming? | Product | Before M1 |
| OQ3 | Minimum n8n version to support? | Engineering | Before M1 (suggest ≥1.88 for MCP ecosystem alignment) |
| OQ4 | Which 20 tools for pilot (M4)? | Product | Before M4 |
| OQ5 | Public verified effort: worth it for API tools only? | Leadership | Before M6 |
| OQ6 | Support both production Farm URL and per-customer self-hosted Farm? | Engineering | Credential docs |

---

## 13. References

### Internal

| Resource | Path |
|----------|------|
| MCP Farm architecture | [docs/FARM-ARCHITECTURE.md](./FARM-ARCHITECTURE.md) |
| MCP Farm PRD | [docs/FARM-PRD.md](./FARM-PRD.md) |
| MCP UI client (reference impl) | [mcpfarm-ui/src/lib/mcp.js](../mcpfarm-ui/src/lib/mcp.js) |
| Generic CLI MCP template | [phase2-common/mcp_server_generic.py](../phase2-common/mcp_server_generic.py) |
| Farm deploy guide | [mcpfarm/DEPLOY.md](../mcpfarm/DEPLOY.md) |
| Example MCP server README | [n2yo-mcp/README.md](../n2yo-mcp/README.md) |

### n8n official documentation

| Topic | URL |
|-------|-----|
| Building community nodes | https://docs.n8n.io/integrations/community-nodes/build-community-nodes/ |
| `@n8n/node` CLI | https://docs.n8n.io/integrations/creating-nodes/build/n8n-node/ |
| Submit / verify community nodes | https://docs.n8n.io/integrations/creating-nodes/deploy/submit-community-nodes/ |
| Verification guidelines | https://docs.n8n.io/connect/create-nodes/build-your-node/reference/verification-guidelines |
| Install private nodes | https://docs.n8n.io/integrations/creating-nodes/deploy/install-private-nodes/ |
| Community nodes env vars | https://docs.n8n.io/hosting/configuration/environment-variables/nodes/ |
| Env-managed package install | https://docs.n8n.io/integrations/community-nodes/installation-and-management/environment-variable-installation |
| MCP Server Trigger | https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-langchain.mcptrigger/ |
| n8n Creator Portal | https://creators.n8n.io/nodes |
| n8n-nodes-starter (publish workflow) | https://github.com/n8n-io/n8n-nodes-starter |

### MCP protocol

| Topic | URL |
|-------|-----|
| Streamable HTTP transport | https://modelcontextprotocol.io/specification/2025-03-26/basic/transports |
| Session management | https://modelcontextprotocol.io/specification/2025-03-26/basic/transports#session-management |

### npm provenance (required 2026-05-01)

| Topic | URL |
|-------|-----|
| Generating provenance statements | https://docs.npmjs.com/generating-provenance-statements |
| npm Trusted Publishers | https://docs.npmjs.com/trusted-publishers |

---

## Appendix A — Example generated package.json

```json
{
  "name": "@hackerdogs/n8n-nodes-gitleaks",
  "version": "1.0.0",
  "description": "Gitleaks secret detection via Hackerdogs MCP Farm",
  "license": "MIT",
  "keywords": ["n8n-community-node-package", "gitleaks", "secrets", "hackerdogs"],
  "n8n": {
    "n8nNodesApiVersion": 1,
    "credentials": ["dist/credentials/McpFarmApi.credentials.js"],
    "nodes": ["dist/nodes/Gitleaks/Gitleaks.node.js"]
  },
  "dependencies": {}
}
```

## Appendix B — Example n8n workflow (conceptual)

```
[Manual Trigger] → [Gitleaks: Run Scan] → [IF secrets found] → [Slack / Jira]
                      │
                      credentials: MCP Farm API
                      source_url: https://github.com/org/repo
```

## Appendix C — Network: n8n Docker → local Farm

When n8n runs in Docker and Farm on host:

| n8n location | Farm URL in credential |
|--------------|------------------------|
| Docker Desktop (Mac/Win) | `http://host.docker.internal:8485` |
| Linux Docker | `http://172.17.0.1:8485` or compose service name if same stack |
| Same compose stack | `http://caddy:80` or internal service URL |

---

*Document maintained by Hackerdogs platform team. Update when codegen lands or n8n verification policy changes.*
