# Hackerdogs MCP Server Farm — Architecture Document

**Version:** 1.0
**Date:** 2026-03-29
**Status:** Draft
**Source:** Derived from FARM-PRD.md

---

## Table of Contents

1. [Overview](#1-overview)
2. [System Context](#2-system-context)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Component Architecture](#4-component-architecture)
   - 4.1 [Cloudflare Tunnel](#41-cloudflare-tunnel)
   - 4.2 [Caddy Reverse Proxy](#42-caddy-reverse-proxy)
   - 4.3 [Auth Gateway](#43-auth-gateway)
   - 4.4 [MCP Server Containers](#44-mcp-server-containers)
   - 4.5 [SQLite Database](#45-sqlite-database)
5. [Network Architecture](#5-network-architecture)
6. [Request Flow](#6-request-flow)
7. [Authentication & Authorisation](#7-authentication--authorisation)
8. [API Key Architecture](#8-api-key-architecture)
9. [Dynamic Server Registration](#9-dynamic-server-registration)
10. [Upstream API Key Pass-Through](#10-upstream-api-key-pass-through)
11. [Port Allocation](#11-port-allocation)
12. [Data Architecture](#12-data-architecture)
13. [Security Architecture](#13-security-architecture)
14. [LLM Safety Guardrails](#14-llm-safety-guardrails)
15. [Deployment Architecture](#15-deployment-architecture)
16. [Configuration Management](#16-configuration-management)
17. [Observability](#17-observability)
18. [Resource Sizing](#18-resource-sizing)
19. [Operational Architecture](#19-operational-architecture)
20. [Architecture Decisions](#20-architecture-decisions)

---

## 1. Overview

The Hackerdogs MCP Server Farm is a production-grade, internet-facing deployment of **155+ MCP (Model Context Protocol) security tool servers** behind a unified, authenticated gateway. It is designed to be consumed by AI agents, LLMs, and MCP-compatible clients such as Claude, Cursor, and OpenAI Agents.

### Core Properties

| Property | Description |
|----------|-------------|
| **Single entry point** | All 155+ tools accessible via `https://mcp.hackerdogs.ai/{server-name}/mcp/` |
| **One-command deploy** | `docker compose up -d` starts everything — proxy, auth, tunnel, all servers |
| **API-only management** | No UI. All operations performed via REST API |
| **Stateless tools** | Every MCP server is ephemeral — no persistent state, no shared memory |
| **Transparent to clients** | Clients see standard MCP endpoints — auth, routing, and security are invisible infrastructure |
| **Secure by default** | No direct internet access to any tool. All traffic authenticated before it reaches a server |

### What It Is Not

- Not a web application — there is no browser-facing UI
- Not a managed cloud service — self-hosted on a single machine
- Not a multi-tenant SaaS — it is infrastructure for Hackerdogs' own agents and authorised clients
- Not a Minibridge/Acuvity deployment — all servers are native FastMCP (Python), no Minibridge wrapper

---

## 2. System Context

```
┌─────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL ACTORS                             │
│                                                                     │
│   ┌─────────────┐  ┌─────────────┐  ┌──────────────┐              │
│   │  Claude /   │  │   Cursor /  │  │  Custom AI   │              │
│   │  Claude     │  │   Windsurf  │  │   Agents /   │              │
│   │  Desktop    │  │   (IDE)     │  │   Scripts    │              │
│   └──────┬──────┘  └──────┬──────┘  └──────┬───────┘              │
│          │                │                 │                      │
│          └────────────────┴─────────────────┘                      │
│                           │                                        │
│              HTTPS + Bearer Token + X-* Headers                    │
└───────────────────────────┼────────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │    Cloudflare Edge      │
              │   mcp.hackerdogs.ai     │
              │   (TLS termination)     │
              └─────────────┬───────────┘
                            │
                    Encrypted Tunnel
                    (outbound-only)
                            │
                            ▼
              ┌─────────────────────────┐
              │    MCP Server Farm      │
              │   (this system)         │
              └─────────────────────────┘
```

### External Dependencies

| Dependency | Purpose | Required |
|------------|---------|----------|
| Cloudflare | TLS termination, tunnel, DDoS protection | Yes |
| Docker Hub (`hackerdogs/*`) | Pre-built MCP server images | Yes |
| Third-party API providers | Shodan, PDCP, Censys, OpenAI, etc. | Per-tool (optional) |

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOCKER COMPOSE STACK                                │
│                        Network: mcpfarm_internal                            │
│                                                                             │
│  ┌─────────────┐     ┌───────────────┐     ┌──────────────────────────┐   │
│  │             │     │               │     │                          │   │
│  │ cloudflared │────▶│     Caddy     │────▶│      auth-gateway        │   │
│  │  (tunnel)   │     │  (proxy :80)  │     │   (FastAPI admin :9090)  │   │
│  │             │     │               │     │                          │   │
│  └─────────────┘     └───────┬───────┘     └────────────┬─────────────┘   │
│                              │                          │                  │
│                              │                   ┌──────┴──────┐          │
│                              │                   │  SQLite DB  │          │
│                              │                   │  (WAL mode) │          │
│                              │                   │  /data/     │          │
│                              │                   └─────────────┘          │
│                              │                                             │
│            ┌─────────────────┼──────────────────────────┐                 │
│            │                 │                          │                 │
│            ▼                 ▼                          ▼                 │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐            │
│  │  naabu-mcp   │  │   trivy-mcp      │  │  metasploit-mcp  │  ...155+   │
│  │  :8105       │  │   :8150          │  │  :8245           │            │
│  └──────────────┘  └──────────────────┘  └──────────────────┘            │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │  (Optional) Tool-Call Guard — PolicyLayer Intercept / AvaKill    │     │
│  └──────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  Volumes:  auth_data (SQLite)  │  caddy_routes (routes.conf)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Component Architecture

### 4.1 Cloudflare Tunnel

**What it does:** Establishes an outbound-only encrypted connection from the host to Cloudflare's edge network. Cloudflare resolves `mcp.hackerdogs.ai` and forwards traffic down the tunnel.

**Why it matters:**
- The host machine opens **zero inbound ports**
- No firewall rules needed
- Cloudflare provides free DDoS mitigation and TLS termination
- The farm's real IP address is never exposed

**Configuration:**
```yaml
# docker-compose.yml
cloudflared:
  image: cloudflare/cloudflared:latest
  command: tunnel run
  environment:
    - TUNNEL_TOKEN=${TUNNEL_TOKEN}
  networks:
    - mcpfarm
  depends_on:
    - caddy
```

**Traffic path:** `Cloudflare Edge → cloudflared container → caddy:80`

---

### 4.2 Caddy Reverse Proxy

**What it does:** Single ingress point for all MCP traffic. Receives every request from cloudflared, validates authentication via the auth gateway, strips the server-name prefix from the URL, and forwards the request to the correct MCP container.

**Key responsibilities:**
- Pattern-match URLs to identify target server (`/naabu-mcp/*` → `naabu-mcp:8105`)
- Delegate authentication to the auth gateway via `forward_auth`
- Strip path prefix before proxying (e.g. `/naabu-mcp/mcp/` → `/mcp/`)
- Hot-reload routing config when new servers are registered

**Caddyfile structure:**
```
:80 {
    # Public health check
    handle /health { respond "OK" 200 }

    # Admin API (auth-gateway enforces its own X-Admin-Secret)
    handle /admin/* { reverse_proxy auth-gateway:9090 }

    # Public server registry
    handle /services { reverse_proxy auth-gateway:9090 }

    # All MCP server routes (auto-generated, 155+ entries)
    import /etc/caddy/routes.conf
}
```

**Auto-generated route block (per server):**
```
@naabu-mcp path /naabu-mcp/*
handle @naabu-mcp {
    forward_auth auth-gateway:9090 {
        uri /verify
        copy_headers Authorization
    }
    uri strip_prefix /naabu-mcp
    reverse_proxy naabu-mcp:8105
}
```

**Why Caddy over Nginx/Traefik:**
- Native `forward_auth` directive — no plugins or Lua scripting
- Hot-reload via admin API (`POST http://caddy:2019/load`)
- Simple declarative config — 155+ routes from a generated file, not 155+ manual blocks

---

### 4.3 Auth Gateway

**What it does:** A lightweight FastAPI microservice that is the sole management plane for the entire farm. There is no UI — everything is a REST API call.

**Responsibilities:**

| Responsibility | How |
|----------------|-----|
| Token verification | `GET /verify` — called by Caddy on every request |
| API key management | Full CRUD via `/admin/keys` |
| Server registry | Tracks all static and dynamic servers |
| Dynamic server management | Launches/stops containers via Docker SDK |
| Health monitoring | Pings every server's `/mcp/` endpoint every 30 seconds |
| Audit logging | Writes every request to `request_log` table |
| Caddy hot-reload | Regenerates `routes.conf` and signals Caddy when servers change |

**Internal architecture:**

```
auth-gateway (FastAPI)
├── main.py           — all route handlers
├── models.py         — SQLite schema (SQLModel / SQLAlchemy)
├── docker_manager.py — Docker SDK wrapper for dynamic containers
├── caddy_reload.py   — routes.conf generation + Caddy reload signal
├── rate_limiter.py   — in-memory sliding window rate limiter
└── seed.py           — first-boot: seed static servers + first admin key
```

**Docker socket access:** The auth-gateway mounts `/var/run/docker.sock` to manage containers for dynamic server registration. This is the only container with Docker access.

---

### 4.4 MCP Server Containers

**What they are:** Each security tool (nmap, trivy, metasploit, etc.) runs as an independent, isolated Docker container built from `hackerdogs/{name}-mcp:latest`.

**Container specification:**

| Property | Value |
|----------|-------|
| Base image | `python:3.11-slim` or `python:3.12-slim` |
| Transport | `streamable-http` (FastMCP) |
| Framework | FastMCP (Python) |
| Process model | Single process — FastMCP handles both stdio and HTTP in one |
| User | Non-root (security hardening) |
| Init | `tini` (proper signal handling) |
| Health endpoint | `GET /mcp/` — returns MCP capability negotiation |
| Exposed ports | None to host — internal Docker network only |

**Environment variables (set by compose/dynamic registration):**
```bash
MCP_TRANSPORT=streamable-http
MCP_PORT=8105          # unique per server
```

**What each server looks like internally:**
```python
# Every server follows this pattern
from mcp.server.fastmcp import FastMCP
from request_env import get_subprocess_env   # per-request env isolation

mcp = FastMCP("naabu-mcp")

@mcp.tool()
async def run_naabu(arguments: str) -> str:
    proc = await asyncio.create_subprocess_exec(
        "naabu", *arguments.split(),
        env=get_subprocess_env()   # injects user's upstream API keys
    )
    stdout, _ = await proc.communicate()
    return stdout.decode()
```

**Compliance test (5 steps each server must pass):**

| Step | Test |
|------|------|
| 1 | Docker image exists |
| 2 | Stdio transport — `tools/list` returns valid JSON-RPC response |
| 3 | Stdio transport — `tools/call` executes and returns result |
| 4 | HTTP streamable — `tools/list` returns valid response |
| 5 | HTTP streamable — `tools/call` executes and returns result |

---

### 4.5 SQLite Database

**What it stores:** All persistent state for the entire farm lives in a single SQLite file at `/data/auth.db`, mounted as a Docker volume.

**Why SQLite:**
- No external database service to manage
- WAL mode handles thousands of concurrent reads with sub-millisecond token lookups
- Single file — trivial to back up (`cp auth.db auth.db.bak`)
- Scalable path: migrate to Turso (distributed SQLite) or Postgres with zero code changes

**Schema:**
```sql
-- API tokens (one row per issued key)
CREATE TABLE api_keys (
    id          TEXT PRIMARY KEY,
    key_hash    TEXT NOT NULL UNIQUE,   -- SHA-256, never store plaintext
    key_prefix  TEXT NOT NULL,          -- e.g. "hd_sk_9f" for display
    name        TEXT NOT NULL,
    owner       TEXT,
    scopes      TEXT DEFAULT '*',       -- '*' = all, or CSV of server names
    rate_limit  INTEGER DEFAULT 100,    -- requests per minute
    is_active   BOOLEAN DEFAULT 1,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at  DATETIME,
    last_used   DATETIME
);

-- Server registry (static + dynamic)
CREATE TABLE servers (
    name        TEXT PRIMARY KEY,
    image       TEXT NOT NULL,
    port        INTEGER NOT NULL UNIQUE,
    env         TEXT DEFAULT '{}',      -- JSON: upstream env var names
    status      TEXT DEFAULT 'running',
    source      TEXT DEFAULT 'static',  -- 'static' or 'dynamic'
    category    TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_health DATETIME,
    health_ok   BOOLEAN DEFAULT 0
);

-- Per-request audit trail
CREATE TABLE request_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id      TEXT REFERENCES api_keys(id),
    server      TEXT NOT NULL,
    method      TEXT,
    status      INTEGER,
    latency_ms  INTEGER,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. Network Architecture

```
┌─────────────────────────────────────────────────┐
│           Docker Network: mcpfarm_internal       │
│                  (bridge driver)                 │
│                                                  │
│  cloudflared ──▶ caddy:80                        │
│                     │                            │
│                     ├──▶ auth-gateway:9090       │
│                     │        │                   │
│                     │    [SQLite]                │
│                     │                            │
│                     ├──▶ naabu-mcp:8105          │
│                     ├──▶ trivy-mcp:8150          │
│                     ├──▶ nuclei-mcp:8155         │
│                     ├──▶ metasploit-mcp:8245     │
│                     └──▶ ... (155+ more)         │
│                                                  │
│  Host ports exposed: NONE                        │
│  (cloudflared connects outbound to Cloudflare)   │
└─────────────────────────────────────────────────┘
```

**Network isolation rules:**
- MCP server containers cannot reach each other (no server-to-server calls)
- MCP server containers cannot reach the auth-gateway or Caddy directly
- Only Caddy can route to MCP servers
- Only the auth-gateway has Docker socket access
- No container has a port bound to the host machine

---

## 6. Request Flow

### Standard Tool Call

```
Step 1 — Client sends request
─────────────────────────────
POST https://mcp.hackerdogs.ai/naabu-mcp/mcp/
Authorization: Bearer hd_sk_a1b2c3d4...
Content-Type: application/json
Body: {"jsonrpc":"2.0","id":1,"method":"tools/call",
       "params":{"name":"run_naabu","arguments":{"arguments":"-host 10.0.0.1"}}}


Step 2 — Cloudflare Edge
─────────────────────────────
TLS termination. Forwards plaintext HTTP down the cloudflared tunnel.


Step 3 — cloudflared → Caddy:80
─────────────────────────────
Tunnel delivers request to Caddy on the internal Docker network.


Step 4 — Caddy: route matching
─────────────────────────────
URL /naabu-mcp/mcp/ matches @naabu-mcp pattern in routes.conf.
Caddy calls forward_auth before proxying.


Step 5 — Caddy calls auth-gateway: /verify
─────────────────────────────
GET auth-gateway:9090/verify
Authorization: Bearer hd_sk_a1b2c3d4...

Auth gateway checks (all must pass):
  ✓ Token exists in api_keys (SHA-256 lookup)
  ✓ is_active = true
  ✓ expires_at > now (or NULL)
  ✓ scopes includes 'naabu-mcp' (or is '*')
  ✓ rate_limit not exceeded (sliding window)

Returns: 200 OK (pass) or 401/403 (fail)


Step 6 — Caddy proxies to MCP server
─────────────────────────────
Strips /naabu-mcp prefix.
Forwards to naabu-mcp:8105/mcp/ with all original headers intact.


Step 7 — MCP server processes request
─────────────────────────────
Middleware extracts X-* headers → injects into per-request env (contextvars).
FastMCP routes tools/call → run_naabu() function.
Naabu subprocess runs with per-request environment.
Result returned as JSON-RPC response.


Step 8 — Response travels back
─────────────────────────────
naabu-mcp → Caddy → cloudflared → Cloudflare Edge → Client
```

### Failed Authentication

```
Client sends request with invalid/expired/out-of-scope token
    │
    ▼
Caddy → forward_auth → auth-gateway returns 401
    │
    ▼
Caddy returns 401 Unauthorized to client
    │
Request never reaches MCP server container
```

---

## 7. Authentication & Authorisation

### Token Format

```
hd_sk_<32 random hex characters>
e.g. hd_sk_9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c
```

- Generated once, shown once (plaintext never stored)
- SHA-256 hash stored in SQLite
- `key_prefix` (`hd_sk_9f`) stored for identification in logs without exposing the full key

### Verification Flow

```
                   Incoming Bearer token
                          │
                          ▼
                   SHA-256(token)
                          │
                          ▼
              ┌───────────────────────┐
              │  SELECT * FROM        │
              │  api_keys WHERE       │
              │  key_hash = $hash     │
              └──────────┬────────────┘
                         │
              ┌──────────▼────────────┐
              │  Row found?           │──── No ──▶  401 Unauthorized
              └──────────┬────────────┘
                         │ Yes
              ┌──────────▼────────────┐
              │  is_active = true?    │──── No ──▶  403 Forbidden
              └──────────┬────────────┘
                         │ Yes
              ┌──────────▼────────────┐
              │  expires_at > now?    │──── No ──▶  403 Forbidden
              └──────────┬────────────┘
                         │ Yes
              ┌──────────▼────────────┐
              │  scope includes       │
              │  requested server?    │──── No ──▶  403 Forbidden
              └──────────┬────────────┘
                         │ Yes
              ┌──────────▼────────────┐
              │  rate_limit OK?       │──── No ──▶  429 Too Many Requests
              └──────────┬────────────┘
                         │ Yes
                         ▼
              Update last_used, log request → 200 OK
```

### Token Scopes

| Scope value | Meaning |
|-------------|---------|
| `*` | Access to all MCP servers |
| `naabu-mcp,trivy-mcp` | Access to named servers only (CSV) |
| `naabu-mcp` | Single server access |

### Rate Limiting

- Per-key sliding window (default: 100 requests/minute)
- Implemented in-memory — no Redis needed for single-node
- Limit is configurable per key via `PATCH /admin/keys/{id}`

---

## 8. API Key Architecture

### Key Lifecycle

```
POST /admin/keys
      │
      ▼  plaintext key returned ONCE — never again
   Store SHA-256(key) in SQLite
      │
      ▼
Key in use
      │
      ├── PATCH /admin/keys/{id}  — modify scopes, rate limit, expiry
      ├── GET   /admin/keys/{id}/usage — audit usage stats
      │
      ▼
Deactivate: PATCH { "is_active": false }   — immediate effect, no restart
Delete:     DELETE /admin/keys/{id}        — permanent removal
```

### Admin API Reference

#### Key Management

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/admin/keys` | Create key (returns plaintext once) |
| `GET` | `/admin/keys` | List all keys |
| `GET` | `/admin/keys/{id}` | Single key details |
| `PATCH` | `/admin/keys/{id}` | Update scopes, rate limit, active status, expiry |
| `DELETE` | `/admin/keys/{id}` | Permanently revoke key |
| `GET` | `/admin/keys/{id}/usage` | Usage stats by server, time range, status code |

#### Server Management

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin/servers` | List all servers + health status |
| `POST` | `/admin/servers` | Register + launch new server at runtime |
| `GET` | `/admin/servers/{name}` | Single server details |
| `DELETE` | `/admin/servers/{name}` | Stop + deregister dynamic server |
| `POST` | `/admin/servers/{name}/restart` | Restart server container |
| `POST` | `/admin/servers/{name}/start` | Start stopped server |
| `POST` | `/admin/servers/{name}/stop` | Stop without deregistering |
| `GET` | `/admin/servers/{name}/health` | Immediate health check |
| `GET` | `/admin/servers/{name}/logs` | Tail container logs |

#### Farm-Wide

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin/stats` | Total requests, active keys, server counts, uptime |
| `GET` | `/admin/audit` | Query request log (`?key_id=`, `?server=`, `?since=`, `?limit=`) |
| `POST` | `/admin/reload` | Force Caddy route reload |
| `GET` | `/admin/export` | Export full farm config (no secrets) |

#### Public (No Auth Required)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Farm liveness check |
| `GET` | `/services` | All servers with health status |
| `GET` | `/verify` | Token check (called by Caddy internally) |

All admin endpoints require `X-Admin-Secret` header.

---

## 9. Dynamic Server Registration

New MCP servers can be added to a running farm without restarting the compose stack.

### Registration Flow

```
POST /admin/servers
{
  "name": "my-new-mcp",
  "image": "hackerdogs/my-new-mcp:latest",
  "port": 8400,
  "env": { "MY_API_KEY": "..." },
  "category": "custom"
}
        │
        ▼
Auth gateway validates:
  - Port not already in use
  - Name not already registered
  - Image reference is valid
        │
        ▼
Insert row in servers table (source = 'dynamic')
        │
        ▼
Docker SDK: pull image → create container on mcpfarm_internal
  network with MCP_TRANSPORT=streamable-http, MCP_PORT=8400
        │
        ▼
Regenerate routes.conf → add new route block
Signal Caddy to hot-reload config
        │
        ▼
Health-check loop picks up new server
Marks healthy once GET /mcp/ responds
        │
        ▼
Server available at:
https://mcp.hackerdogs.ai/my-new-mcp/mcp/
```

### Persistence of Dynamic Servers

- Dynamic servers are **not in docker-compose.yml**
- They survive auth-gateway restarts (re-launched from `source='dynamic'` rows in SQLite on startup)
- They do **not** survive full `docker compose down && up` (must re-register via API, or the startup routine re-creates them from the database)

---

## 10. Upstream API Key Pass-Through

Some tools require third-party API keys (Shodan, PDCP/ProjectDiscovery, Censys, OpenAI, etc.). The farm never stores these keys — they are passed per-request by the client and injected into the tool subprocess for that request only.

### Flow

```
Client MCP Config
─────────────────
{
  "url": "https://mcp.hackerdogs.ai/uncover-mcp/mcp/",
  "headers": {
    "Authorization": "Bearer hd_sk_abc123",       ← farm access token
    "X-SHODAN-API-KEY": "user_shodan_key",         ← user's own Shodan key
    "X-CENSYS-API-TOKEN": "user_censys_token"      ← user's own Censys token
  }
}
        │
        ▼
Caddy passes all headers through untouched
        │
        ▼
MCP Server: Starlette middleware runs on every request
  extracts X-SHODAN-API-KEY → sets SHODAN_API_KEY in contextvars
  extracts X-CENSYS-API-TOKEN → sets CENSYS_API_TOKEN in contextvars
        │
        ▼
Tool function calls get_subprocess_env()
  returns os.environ.copy() + per-request overrides
        │
        ▼
Subprocess runs with user's keys injected as environment variables
Keys exist only for the duration of this one request
Keys are never written to disk or logged
```

### Header-to-Environment Mapping

| HTTP Header | Environment Variable | Used by |
|-------------|---------------------|---------|
| `X-PDCP-API-KEY` | `PDCP_API_KEY` | cvemap, nuclei, naabu |
| `X-SHODAN-API-KEY` | `SHODAN_API_KEY` | uncover, shodan |
| `X-CENSYS-API-TOKEN` | `CENSYS_API_TOKEN` | uncover, censys |
| `X-OPENAI-API-KEY` | `OPENAI_API_KEY` | openrisk, ai tools |
| `X-ANTHROPIC-API-KEY` | `ANTHROPIC_API_KEY` | ai tools |

### Fallback Chain

```
1. Per-request header (user's own key, highest priority)
       ↓ if not provided
2. Container environment variable (farm-level default from .env)
       ↓ if not set
3. None — server warns and degrades gracefully
```

### Per-Request Isolation

Uses Python `contextvars` — concurrent requests from different users with different keys never interfere. User A's Shodan key cannot leak into User B's simultaneous request.

---

## 11. Port Allocation

```
Port Range   Category                    Example Servers
──────────   ─────────────────────────   ──────────────────────────────
8100–8119    Core / Phase 1 tools        julius-mcp, augustus-mcp, naabu-mcp
8120–8149    Network recon               rustscan-mcp, zmap-mcp, fping-mcp
8150–8179    Vulnerability scanning      trivy-mcp, grype-mcp, nikto-mcp, nuclei-mcp
8180–8209    Web application testing     dalfox-mcp, wfuzz-mcp, xsstrike-mcp, sqlmap-mcp
8210–8239    OSINT                       sherlock-mcp, maigret-mcp, holehe-mcp, ghunt-mcp
8240–8269    Exploitation / Post-exploit metasploit-mcp, hydra-mcp, john-mcp, hashcat-mcp
8270–8299    Cloud / Container security  kube-hunter-mcp, trivy-mcp, checkov-mcp
8300–8329    Binary analysis / RE        ghidra-mcp, radare2-mcp, cutter-mcp, binwalk-mcp
8330–8359    Network attacks / Wireless  bettercap-mcp, ettercap-mcp, aircrack-ng-mcp
8360–8399    Misc / Overflow             remaining static servers
8400–8499    ★ RESERVED — Dynamic        added via POST /admin/servers at runtime
```

A canonical `port-map.json` is the single source of truth. The compose generator script reads it to produce `docker-compose.yml` and `caddy/routes.conf`.

---

## 12. Data Architecture

### Data Flow

```
Client request
      │
      ▼
auth-gateway writes to request_log (key_id, server, method, status, latency)
      │
      ▼
MCP server executes tool (no persistent writes — stateless)
      │
      ▼
Response returned
```

### Storage Summary

| Data | Location | Persistent | Backed Up |
|------|----------|------------|-----------|
| API keys (hashed) | SQLite `api_keys` | Yes (volume) | Recommended |
| Server registry | SQLite `servers` | Yes (volume) | Recommended |
| Audit/request log | SQLite `request_log` | Yes (volume) | Optional |
| Upstream API keys | Never stored | N/A | N/A |
| Tool outputs | Never stored | N/A | N/A |
| Rate limit counters | In-memory (auth-gateway) | No | N/A |
| Caddy routes | Shared volume `caddy_routes` | Regenerated | No |

### Backup Strategy

```bash
# Back up the entire farm state — one file
cp /var/lib/docker/volumes/mcpfarm_auth_data/_data/auth.db auth.db.$(date +%Y%m%d)
```

---

## 13. Security Architecture

### Defence Layers

```
Layer 0 — Host
  No open inbound ports on the host machine.
  cloudflared is outbound-only — no firewall rules needed.
  Real IP never exposed.

Layer 1 — Network
  All containers on private Docker bridge (mcpfarm_internal).
  MCP servers cannot directly communicate with each other.
  No container has host-bound ports.

Layer 2 — TLS
  Cloudflare terminates TLS at the edge.
  Internal Docker traffic is unencrypted (trusted private network).

Layer 3 — Authentication
  Every request verified by auth-gateway via Caddy forward_auth.
  SHA-256 token hashing — plaintext never stored.
  Single-lookup per request (~0.01ms with indexed SQLite).

Layer 4 — Authorisation
  Per-key scopes restrict which servers a token can access.
  Per-key rate limits prevent abuse.
  Expiry timestamps enforced on every request.
  Instant revocation via PATCH { "is_active": false }.

Layer 5 — Container Isolation
  Each tool runs as a non-root user.
  No shared volumes between MCP server containers.
  tini init process for proper signal handling.
  Stateless — no data persisted between requests.

Layer 6 — LLM Tool-Call Guard (recommended)
  PolicyLayer Intercept or AvaKill as MCP-native firewall.
  Blocks dangerous tool invocations before they reach containers.
  Always on — invisible to users.
```

### Key Rotation

```bash
# 1. Create new key
curl -X POST https://mcp.hackerdogs.ai/admin/keys \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -d '{"name": "team-key-v2", "scopes": "*"}'

# 2. Distribute new key to users

# 3. Revoke old key (immediate effect)
curl -X PATCH https://mcp.hackerdogs.ai/admin/keys/{old_id} \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -d '{"is_active": false}'
```

### Upstream Key Security

- Never stored on the farm
- In-transit: encrypted via Cloudflare Tunnel
- In-memory: isolated per-request via `contextvars`
- In logs: Caddy access logs must be configured to redact `X-*` headers
- After request: gone

---

## 14. LLM Safety Guardrails

MCP servers execute real security tools. An LLM under prompt injection could invoke destructive operations against unintended targets. A guardrail layer intercepts tool calls before they reach the servers.

### Recommended Architecture (Defence in Depth)

```
LLM / AI Agent
      │
      ▼
┌─────────────────────────────────────┐
│ Layer 1: InferShield (MIT)          │
│ Sits between agent and LLM API      │
│ Catches: prompt injection, PII      │
│ leakage, encoded attacks            │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ Layer 2: LlamaFirewall (Meta/MIT)   │
│ Scans LLM output before tool calls  │
│ Catches: goal misalignment,         │
│ chain-of-thought attacks            │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ Layer 3: PolicyLayer Intercept      │
│ (Apache 2.0) — MCP tool-call        │
│ firewall. YAML policies. <1ms.      │
│ Catches: unauthorised tools,        │
│ dangerous arguments, rate abuse     │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ Layer 4: Caddy + Auth Gateway       │
│ Bearer token, scopes, rate limits,  │
│ network isolation                   │
└──────────────────┬──────────────────┘
                   │
                   ▼
            MCP Server Farm
```

### Guardrail Tool Comparison

| Tool | License | MCP-Native | ML Required | Latency | Best For |
|------|---------|------------|-------------|---------|----------|
| PolicyLayer Intercept | Apache 2.0 | Yes | No | <1ms | Primary tool-call firewall |
| AvaKill | AGPL-3.0 | Yes | No | <1ms | Tool-call firewall + OS sandbox |
| mcpwall | Apache 2.0 | Yes | No | <1ms | Lightweight alternative |
| IronCurtain | Apache 2.0 | Yes | No (one-time) | <1ms | Natural-language policies |
| LlamaFirewall | MIT | No | Yes | ~100ms | Prompt injection + alignment |
| NeMo Guardrails | Apache 2.0 | Partial | Optional | ~200ms | Conversation-level safety |
| InferShield | MIT | No | Heuristic | Low | LLM API input/output scanning |

### Recommended v1 Configuration

Start with two layers:
1. **PolicyLayer Intercept** — deploy as container in the compose stack, YAML policies for allowed tools and argument constraints
2. **LlamaFirewall** — deployed by the agent operator (optional but recommended for production)

---

## 15. Deployment Architecture

### Directory Structure

```
hd-mcpservers-docker/
│
├── mcpfarm/                        ← farm infrastructure
│   ├── docker-compose.yml          ← generated (155+ services + infra)
│   ├── docker-compose.override.yml ← local overrides
│   ├── .env                        ← secrets (not committed)
│   ├── .env.example                ← template
│   ├── port-map.json               ← source of truth: server → port
│   │
│   ├── caddy/
│   │   ├── Caddyfile               ← reverse proxy config
│   │   └── routes.conf             ← auto-generated per-server routes
│   │
│   ├── auth-gateway/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── docker_manager.py
│   │   ├── caddy_reload.py
│   │   ├── rate_limiter.py
│   │   ├── requirements.txt
│   │   └── seed.py
│   │
│   ├── cloudflared/
│   │   └── (config via TUNNEL_TOKEN env only)
│   │
│   └── scripts/
│       ├── generate-compose.py     ← builds compose + routes from port-map.json
│       └── health-check.sh         ← CLI health check for all servers
│
├── naabu-mcp/                      ← individual server source
│   ├── Dockerfile
│   ├── mcp_server.py
│   ├── requirements.txt
│   ├── docker-compose.yml          ← for standalone testing
│   └── test.sh                     ← 5-step compliance test
│
├── trivy-mcp/                      ← ... (155+ server directories)
│   └── ...
│
└── docs/
    ├── FARM-PRD.md
    └── FARM-ARCHITECTURE.md        ← this document
```

### Compose Service Dependency Graph

```
cloudflared
    └── depends_on: caddy

caddy
    └── depends_on: auth-gateway (healthy)

auth-gateway
    └── (starts independently, seeds database on first boot)

naabu-mcp, trivy-mcp, ... (155+ servers)
    └── (start independently, no inter-service deps)
```

### First-Boot Sequence

```bash
# 1. Clone repo and enter farm directory
git clone https://github.com/hackerdogs-ai/hd-mcpservers-docker.git
cd hd-mcpservers-docker/mcpfarm

# 2. Configure environment
cp .env.example .env
# Edit .env: set TUNNEL_TOKEN, ADMIN_SECRET, optional upstream API keys

# 3. Generate compose file + Caddy routes from port-map.json
python scripts/generate-compose.py

# 4. Pull all pre-built images and start
docker compose pull
docker compose up -d

# 5. Seed first admin API key (one-time)
docker compose exec auth-gateway python seed.py
# Output: Admin key: hd_sk_...  ← store this securely

# 6. Create user-facing API keys
curl -X POST https://mcp.hackerdogs.ai/admin/keys \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -d '{"name": "my-agent", "scopes": "*"}'

# 7. Verify farm is healthy
curl https://mcp.hackerdogs.ai/health
curl https://mcp.hackerdogs.ai/services
```

---

## 16. Configuration Management

### Environment Variables (.env)

```bash
# ── Cloudflare ──
TUNNEL_TOKEN=<cloudflare-tunnel-token>

# ── Auth Gateway ──
ADMIN_SECRET=<random-high-entropy-secret>
AUTH_DB_PATH=/data/auth.db

# ── Upstream API Keys (optional — farm-level defaults) ──
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
PDCP_API_KEY=
SHODAN_API_KEY=
CENSYS_API_TOKEN=
# Users override these per-request via X-* headers
```

### Client Configuration (MCP Client Side)

```json
{
  "mcpServers": {
    "naabu": {
      "url": "https://mcp.hackerdogs.ai/naabu-mcp/mcp/",
      "transport": "streamable-http",
      "headers": {
        "Authorization": "Bearer hd_sk_a1b2c3d4..."
      }
    },
    "uncover": {
      "url": "https://mcp.hackerdogs.ai/uncover-mcp/mcp/",
      "transport": "streamable-http",
      "headers": {
        "Authorization": "Bearer hd_sk_a1b2c3d4...",
        "X-SHODAN-API-KEY": "your_shodan_key"
      }
    }
  }
}
```

### Source of Truth Hierarchy

```
port-map.json
      │ (input to)
      ▼
generate-compose.py
      │ (produces)
      ├──▶ docker-compose.yml  (all 155+ services)
      └──▶ caddy/routes.conf   (all 155+ route blocks)
```

Manual edits to `docker-compose.yml` or `routes.conf` will be overwritten by the next generator run.

---

## 17. Observability

### Health Monitoring

```
GET /health
  → 200 OK if Caddy + auth-gateway are running

GET /services
  → JSON list of all servers with health status
  → auth-gateway pings each server's /mcp/ every 30 seconds
  → Example response:
  {
    "servers": [
      { "name": "naabu-mcp", "status": "healthy", "last_check": "..." },
      { "name": "trivy-mcp", "status": "healthy", "last_check": "..." }
    ],
    "total": 157, "healthy": 155, "unhealthy": 2
  }
```

### Logging

| Component | Output | Format |
|-----------|--------|--------|
| Caddy | stdout | Structured JSON access logs |
| Auth gateway | stdout + SQLite | Structured JSON + request_log table |
| MCP servers | stdout/stderr | Tool output captured by Docker |

**Audit queries:**
```bash
# All calls to naabu-mcp in the last hour
GET /admin/audit?server=naabu-mcp&since=2026-03-29T08:00:00Z

# All calls by a specific key
GET /admin/audit?key_id=a1b2c3d4&limit=100

# Farm-wide stats
GET /admin/stats
```

### Log Aggregation (Optional)

Docker log driver can forward all container logs to:
- Grafana Loki
- AWS CloudWatch
- Splunk
- Any syslog-compatible sink

```yaml
# docker-compose.yml (optional log driver config)
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## 18. Resource Sizing

### Per-Server Footprint

| Resource | Idle | Active (tool running) |
|----------|------|-----------------------|
| Memory | 30–80 MB | 100–500 MB |
| CPU | ~0% | Burst during execution |
| Disk | 0 MB (stateless) | Temp files, cleaned per request |

### Farm Totals

| Resource | Estimate (155 servers) |
|----------|------------------------|
| Memory (all idle) | 8–12 GB |
| Memory (10 concurrent) | 12–16 GB |
| Disk (Docker images) | 40–60 GB |
| CPU (idle) | <1 core |
| CPU (10 concurrent) | 4–8 cores |

### Recommended Host Sizing

| Tier | Spec | Suitable For |
|------|------|-------------|
| Dev / Test | 16 GB RAM, 4 CPU, 100 GB SSD | ~50 servers, internal testing |
| Production | 32 GB RAM, 8 CPU, 200 GB SSD | All 155+ servers |
| High-load | 64 GB RAM, 16 CPU, 500 GB SSD | All servers + concurrent heavy tools |

---

## 19. Operational Architecture

### Common Operations

```bash
# ── Farm Lifecycle ──
docker compose up -d                              # Start farm
docker compose down                               # Stop farm
docker compose pull && docker compose up -d       # Update all images
docker compose restart naabu-mcp                  # Restart one server

# ── Key Management ──
# Issue a key scoped to specific servers
curl -X POST https://mcp.hackerdogs.ai/admin/keys \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -d '{"name": "pentest-agent", "scopes": "naabu-mcp,nuclei-mcp,trivy-mcp", "rate_limit": 200}'

# Revoke a key immediately
curl -X PATCH https://mcp.hackerdogs.ai/admin/keys/{id} \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -d '{"is_active": false}'

# ── Dynamic Server Management ──
# Add new server without restart
curl -X POST https://mcp.hackerdogs.ai/admin/servers \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -d '{"name": "my-new-mcp", "image": "hackerdogs/my-new-mcp:latest", "port": 8400}'

# Remove dynamic server
curl -X DELETE https://mcp.hackerdogs.ai/admin/servers/my-new-mcp \
  -H "X-Admin-Secret: $ADMIN_SECRET"

# ── Audit ──
curl "https://mcp.hackerdogs.ai/admin/audit?server=metasploit-mcp&limit=50" \
  -H "X-Admin-Secret: $ADMIN_SECRET"
```

### Update Strategy

```bash
# Update a single server image with zero downtime
docker pull hackerdogs/naabu-mcp:latest
docker compose up -d --no-deps naabu-mcp

# Update all servers (brief per-server interruption)
docker compose pull && docker compose up -d

# Update infrastructure only (Caddy, auth-gateway)
docker compose up -d --no-deps caddy auth-gateway
```

### Disaster Recovery

```bash
# Restore from SQLite backup
docker compose stop auth-gateway
cp auth.db.backup /var/lib/docker/volumes/mcpfarm_auth_data/_data/auth.db
docker compose start auth-gateway

# Full rebuild (if host is lost)
# 1. Provision new host
# 2. Clone repo, restore .env and auth.db backup
# 3. docker compose pull && docker compose up -d
# Farm is fully restored — all images are on Docker Hub
```

---

## 20. Architecture Decisions

### Why API-Only (No UI)

| Factor | API-Only | Web Dashboard |
|--------|----------|---------------|
| Attack surface | Minimal — single FastAPI service | Frontend adds XSS, CSRF, cookie vectors |
| Automation | Trivially scriptable with curl | Requires browser automation |
| Maintenance | Zero frontend dependencies | Node.js/React build pipeline |
| Target users | DevOps engineers, scripts, agents | General users (not the audience) |

### Why Caddy over Nginx / Traefik

| Feature | Caddy | Nginx | Traefik |
|---------|-------|-------|---------|
| Native forward_auth | Yes | No (needs Lua/module) | Yes |
| Hot-reload API | Yes (POST /load) | No (SIGHUP) | Yes |
| Config simplicity | Caddyfile | Complex blocks | YAML labels |
| Dynamic config | Generated file + reload | Same | Service-discovery based |

### Why SQLite over Postgres / Redis

| Factor | SQLite | Postgres | Redis |
|--------|--------|----------|-------|
| Extra services | None | 1 extra container | 1 extra container |
| Token lookup speed | ~0.01ms (indexed) | ~0.5ms | ~0.1ms |
| Backup | Copy one file | pg_dump | RDB/AOF |
| Scaling path | Turso / LiteFS | Already there | Already there |

### Why Hackerdogs Images Only (No Minibridge/Acuvity)

The farm requires a uniform contract from every server:
- One container, one port, one process
- `/mcp/` endpoint for both health checks and traffic
- `hackerdogs/*-mcp:latest` image naming

Acuvity/Minibridge images expose `/sse` or `/mcp` at `:8000` with a two-process model (Go Minibridge + child). Supporting them would require branching logic in Caddy routes, health checks, and the server registry. The decision to use only Hackerdogs-built FastMCP images keeps the entire farm uniform and eliminates special-case handling.

### Why Cloudflare Tunnel over Direct Expose

| Factor | Cloudflare Tunnel | Direct Expose |
|--------|-------------------|---------------|
| Inbound ports on host | None | 443 required |
| TLS management | Cloudflare handles | Cert renewal needed |
| DDoS mitigation | Free (Cloudflare) | Host responsibility |
| Real IP exposure | Hidden | Exposed |
| Cost | Free tier | Same |

---

*This document reflects the architecture as defined in FARM-PRD.md. Implementation status of individual components may vary. Refer to test-failures-report.md for current server compliance status.*
