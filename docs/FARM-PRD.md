# PRD: Hackerdogs MCP Server Farm

> **Canonical architecture & product framing:** [AI-aware zero-trust gateway for MCP](./AI-aware-zero-trust-gateway-for-MCP.md). This PRD is supporting implementation detail (compose, admin API, guardrail research). If anything disagrees, the gateway spec wins. **Persistence:** the gateway spec standardizes **PostgreSQL + TimescaleDB** ([`docs/schema/mcp-farm-timescaledb.sql`](./schema/mcp-farm-timescaledb.sql)) for production; SQLite below remains a minimal-dev alternative, not the long-term target.

## 1. Overview

A self-contained, stateless, isolated deployment of **155+ MCP (Model Context Protocol) security tool servers** behind a single Caddy reverse proxy, exposed to the internet via Cloudflare Tunnel at `mcp.hackerdogs.ai`, authenticated via API Key Bearer tokens stored in SQLite. The entire farm launches with a single `docker compose up` command and is ready for any MCP client or LLM to access over HTTP in seconds.

**The farm is entirely API-driven.** There is no web UI, no dashboard, no admin panel. All management — key provisioning, server registration, health checks, usage stats — is performed through the admin REST API. This keeps the attack surface minimal and makes the farm fully automatable by scripts, CI/CD pipelines, and other agents.

**Transparent to users.** From a user's perspective, every server in the farm is just another MCP endpoint — no different from any standalone MCP server they'd run locally. The authentication, the reverse proxy, the tool-call firewall, the rate limiting — all of it is invisible infrastructure. Users never install anything special, never configure a "farm client," and never opt into security features. They point their MCP client at a URL, provide their Bearer token and any upstream API keys the tool needs, and it works. The security is a property of the infrastructure, not a burden on the user.

---

## 2. Goals

| Goal | Description |
|------|-------------|
| **One-command deploy** | `docker compose up -d` brings up the entire farm — all 155+ MCP servers, Caddy, auth gateway, and Cloudflare tunnel |
| **Seconds to ready** | Pre-built images from `hackerdogs/*-mcp:latest` on Docker Hub; no build step in production |
| **Self-contained** | Everything runs inside Docker; zero host dependencies beyond Docker Engine + Compose |
| **Stateless & isolated** | Each MCP server is an independent container with no shared state; the only persistent state is the SQLite auth database (a single mounted volume) |
| **Secure by default** | No MCP server is directly accessible; all traffic flows through Caddy with mandatory Bearer token authentication |
| **Scalable auth** | Token management via admin API; SQLite with WAL mode handles high-concurrency reads; horizontally scalable by adding farm replicas behind a load balancer |
| **API-only management** | Zero UI. All operations (keys, servers, health, usage) exposed exclusively as REST endpoints |
| **Dynamic server registration** | New MCP servers can be added to the running farm via the admin API without restarting the entire compose stack |
| **Transparent to users** | From the user's perspective, each server is just a standard MCP endpoint — the farm, firewall, auth, and proxy are invisible infrastructure |
| **LLM safety guardrails** | Inline prompt firewall / tool-call guard between LLMs and MCP servers — always on, invisible to users, no opt-in required |

---

## 3. Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                              DOCKER COMPOSE NETWORK                                  │
│                            (mcpfarm_internal, bridge)                                │
│                                                                                      │
│  ┌──────────────┐    ┌───────────────┐    ┌────────────────┐                         │
│  │              │    │               │    │                │                         │
│  │  cloudflared │───▶│    Caddy      │───▶│  auth-gateway  │                         │
│  │  (tunnel)    │    │  (reverse     │    │  (API-only     │                         │
│  │              │    │   proxy)      │    │   admin + auth)│                         │
│  └──────────────┘    │               │    │                │                         │
│                      │  :80          │    │  :9090         │                         │
│                      └───────┬───────┘    └────────┬───────┘                         │
│                              │                     │                                 │
│                              │              ┌──────┴───────┐                         │
│                              │              │  SQLite DB   │                         │
│                              │              │  (WAL mode)  │                         │
│                              │              │  /data/       │                         │
│                              │              │  ├─ auth.db   │                         │
│                              │              │  └─ registry  │                         │
│                              │              └──────────────┘                         │
│                              │                                                       │
│            ┌─────────────────┼──────────────────┐                                    │
│            │                 │                   │                                    │
│            ▼                 ▼                   ▼                                    │
│  ┌─────────────────┐ ┌──────────────┐ ┌─────────────────┐                            │
│  │  julius-mcp     │ │ naabu-mcp    │ │ trivy-mcp       │  ... 155+ servers         │
│  │  :8100          │ │ :8105        │ │ :8150           │  (+ dynamically added)    │
│  └─────────────────┘ └──────────────┘ └─────────────────┘                            │
│                                                                                      │
│  ┌───────────────────────────────────────────────────┐                               │
│  │  (Optional) Tool-Call Guard / Prompt Firewall     │                               │
│  │  AvaKill / PolicyLayer Intercept / IronCurtain    │                               │
│  │  See Section 11: LLM Safety Guardrails            │                               │
│  └───────────────────────────────────────────────────┘                               │
└──────────────────────────────────────────────────────────────────────────────────────┘
                              │
                              │ Cloudflare Tunnel
                              ▼
                    ┌─────────────────────┐
                    │  mcp.hackerdogs.ai  │
                    │  (Cloudflare Edge)  │
                    └─────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │  MCP Clients / LLMs │
                    │  (Claude, Cursor,   │
                    │   OpenAI, etc.)     │
                    └─────────────────────┘
```

### 3.1 Request Flow

```
1. Client sends request:
   POST https://mcp.hackerdogs.ai/naabu-mcp/mcp/
   Authorization: Bearer hd_sk_abc123...
   Content-Type: application/json

2. Cloudflare Edge → cloudflared container → Caddy :80

3. Caddy:
   a. Strips /naabu-mcp prefix, extracts upstream service name
   b. Calls forward_auth to auth-gateway:9090/verify
      - Passes Authorization header
      - auth-gateway checks token in SQLite
      - Returns 200 (valid) or 401 (invalid)
   c. If 200: reverse_proxy to naabu-mcp:8105
   d. If 401: returns 401 Unauthorized to client

4. MCP server processes request, returns response back through Caddy
```

### 3.2 URL Scheme

Every MCP server is accessible at a predictable URL:

```
https://mcp.hackerdogs.ai/{server-name}/mcp/
```

Examples:
- `https://mcp.hackerdogs.ai/naabu-mcp/mcp/` — Naabu port scanner
- `https://mcp.hackerdogs.ai/trivy-mcp/mcp/` — Trivy vulnerability scanner
- `https://mcp.hackerdogs.ai/nuclei-mcp/mcp/` — Nuclei scanner
- `https://mcp.hackerdogs.ai/sherlock-mcp/mcp/` — Sherlock username finder

The `/mcp/` suffix is the standard streamable-http endpoint that FastMCP exposes.

---

## 4. Components

### 4.1 Caddy Reverse Proxy

**Role:** Single ingress point for all MCP traffic. Handles routing and delegates authentication. No TLS termination needed — Cloudflare tunnel handles external TLS, and all internal traffic is on a private Docker bridge network.

**Why Caddy:**
- Native `forward_auth` directive (no Lua/plugins needed)
- Simple, declarative Caddyfile configuration
- Supports dynamic config reload via API (`POST /load`) for hot-adding new server routes
- Wildcard path matching for 155+ services without manual per-service config

**Caddyfile Design (dynamic routing):**

```caddyfile
{
    admin off
    auto_https off
}

:80 {
    handle /health {
        respond "OK" 200
    }

    # Admin API pass-through (admin-secret checked by auth-gateway itself)
    handle /admin/* {
        reverse_proxy auth-gateway:9090
    }

    # Service registry (no auth — returns public server list)
    handle /services {
        reverse_proxy auth-gateway:9090
    }

    # Auto-generated per-server routes (imported from routes.conf)
    import /etc/caddy/routes.conf
}
```

> Routes are auto-generated into `routes.conf` and can be hot-reloaded when new servers are registered via the admin API. See Section 5 (Dynamic Server Registration).

### 4.2 Auth Gateway (API-Only)

A lightweight FastAPI microservice. **There is no UI.** Every operation is a REST API call. This is the single management plane for the entire farm.

**Responsibilities:**

1. **Token validation** — `GET /verify` checks `Authorization: Bearer <token>` against SQLite (called by Caddy `forward_auth`)
2. **API key management** — Full CRUD for API keys
3. **Server registry** — Tracks all MCP servers (both static compose entries and dynamically added ones)
4. **Dynamic server registration** — Add/remove MCP servers at runtime
5. **Health monitoring** — Periodic health checks of all registered servers
6. **Usage & audit** — Per-key, per-server request logging in SQLite

**Database schema (SQLite with WAL):**

```sql
-- ── API Keys ──
CREATE TABLE api_keys (
    id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    key_hash    TEXT NOT NULL UNIQUE,
    key_prefix  TEXT NOT NULL,
    name        TEXT NOT NULL,
    owner       TEXT,
    scopes      TEXT DEFAULT '*',
    rate_limit  INTEGER DEFAULT 100,
    is_active   BOOLEAN DEFAULT 1,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at  DATETIME,
    last_used   DATETIME
);

CREATE INDEX idx_key_hash ON api_keys(key_hash);
CREATE INDEX idx_active ON api_keys(is_active);

-- ── Server Registry ──
CREATE TABLE servers (
    name        TEXT PRIMARY KEY,
    image       TEXT NOT NULL,
    port        INTEGER NOT NULL UNIQUE,
    env         TEXT DEFAULT '{}',
    status      TEXT DEFAULT 'running' CHECK(status IN ('running','stopped','starting','error')),
    source      TEXT DEFAULT 'static' CHECK(source IN ('static','dynamic')),
    category    TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_health DATETIME,
    health_ok   BOOLEAN DEFAULT 0
);

CREATE INDEX idx_server_status ON servers(status);

-- ── Request Log ──
CREATE TABLE request_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id      TEXT REFERENCES api_keys(id),
    server      TEXT NOT NULL,
    method      TEXT,
    status      INTEGER,
    latency_ms  INTEGER,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_request_log_key ON request_log(key_id, created_at);
CREATE INDEX idx_request_log_time ON request_log(created_at);
```

**API Key format:** `hd_sk_<32 random hex chars>` (e.g., `hd_sk_a1b2c3d4e5f6...`)

### 4.3 Complete Admin API Reference

All admin endpoints require `X-Admin-Secret` header (matches `ADMIN_SECRET` env var). There is no web interface.

#### Key Management

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/admin/keys` | Create new API key (returns plaintext key once, stores SHA-256 hash) |
| `GET` | `/admin/keys` | List all keys (prefix, name, scopes, rate_limit, active, last_used) |
| `GET` | `/admin/keys/{id}` | Get single key details |
| `PATCH` | `/admin/keys/{id}` | Update scopes, rate_limit, is_active, expires_at |
| `DELETE` | `/admin/keys/{id}` | Permanently revoke and delete a key |
| `GET` | `/admin/keys/{id}/usage` | Usage stats: request counts by server, time range, status codes |

**Create key request:**
```bash
curl -X POST https://mcp.hackerdogs.ai/admin/keys \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pentesting-agent",
    "owner": "team@hackerdogs.ai",
    "scopes": "naabu-mcp,trivy-mcp,nuclei-mcp",
    "rate_limit": 200,
    "expires_at": "2026-12-31T23:59:59Z"
  }'
```

**Create key response (key shown once, never again):**
```json
{
  "id": "a1b2c3d4e5f6...",
  "key": "hd_sk_9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c",
  "key_prefix": "hd_sk_9f",
  "name": "pentesting-agent",
  "scopes": "naabu-mcp,trivy-mcp,nuclei-mcp",
  "rate_limit": 200,
  "created_at": "2026-03-14T12:00:00Z",
  "expires_at": "2026-12-31T23:59:59Z"
}
```

#### Dynamic Server Management

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin/servers` | List all registered servers (static + dynamic) with health status |
| `POST` | `/admin/servers` | Register and launch a new MCP server at runtime |
| `GET` | `/admin/servers/{name}` | Get details for a single server |
| `DELETE` | `/admin/servers/{name}` | Stop and deregister a dynamically-added server |
| `POST` | `/admin/servers/{name}/restart` | Restart a server container |
| `POST` | `/admin/servers/{name}/stop` | Stop a server without deregistering |
| `POST` | `/admin/servers/{name}/start` | Start a stopped server |
| `GET` | `/admin/servers/{name}/health` | Immediate health check (bypass cache) |
| `GET` | `/admin/servers/{name}/logs` | Tail recent container logs (last N lines) |

**Register new server request:**
```bash
curl -X POST https://mcp.hackerdogs.ai/admin/servers \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-custom-mcp",
    "image": "hackerdogs/my-custom-mcp:latest",
    "port": 8400,
    "env": {
      "CUSTOM_API_KEY": "sk-..."
    },
    "category": "custom"
  }'
```

**Register new server response:**
```json
{
  "name": "my-custom-mcp",
  "image": "hackerdogs/my-custom-mcp:latest",
  "port": 8400,
  "status": "starting",
  "url": "https://mcp.hackerdogs.ai/my-custom-mcp/mcp/",
  "source": "dynamic",
  "created_at": "2026-03-14T14:30:00Z"
}
```

#### Farm-Wide Operations

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin/stats` | Farm-wide stats: total requests, active keys, server counts, uptime |
| `GET` | `/admin/audit` | Query the request_log (supports `?key_id=`, `?server=`, `?since=`, `?limit=`) |
| `POST` | `/admin/reload` | Force Caddy route reload (after dynamic server changes) |
| `GET` | `/admin/export` | Export full farm configuration (servers + keys metadata, no secrets) |

#### Public Endpoints (No Admin Secret Required)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Farm health (200 OK if Caddy + auth-gateway are up) |
| `GET` | `/services` | List all available servers with health status (public, no auth) |
| `GET` | `/verify` | Token verification (called internally by Caddy forward_auth) |

### 4.4 Cloudflare Tunnel (cloudflared)

A `cloudflare/cloudflared` container that establishes an outbound-only encrypted tunnel to Cloudflare's edge network.

**Configuration:**
- Tunnel points to `caddy:80` inside the Docker network
- DNS record: `mcp.hackerdogs.ai` → Cloudflare Tunnel
- No inbound ports opened on the host machine

**Tunnel config (`/etc/cloudflared/config.yml`):**

```yaml
tunnel: <TUNNEL_ID>
credentials-file: /etc/cloudflared/credentials.json

ingress:
  - hostname: mcp.hackerdogs.ai
    service: http://caddy:80
    originRequest:
      noTLSVerify: true
  - service: http_status:404
```

### 4.5 MCP Server Containers (155+)

Each MCP server runs as an independent container:

- **Image:** `hackerdogs/{name}-mcp:latest` (pre-built on Docker Hub)
- **Transport:** `streamable-http` (set via `MCP_TRANSPORT` env var)
- **Port:** Unique per server (8100–8399 range)
- **Runtime:** Non-root user, tini init, Python 3.11/3.12
- **No exposed host ports** — only reachable within the Docker network via Caddy
- **Health check:** Each server exposes `/mcp/` which returns the MCP capability negotiation

---

## 5. Dynamic Server Registration

One of the key capabilities: new MCP servers can be added to the running farm without restarting the compose stack or editing YAML files. Everything is done via the admin API.

### 5.1 How It Works

```
Admin calls POST /admin/servers with image, name, port
    │
    ▼
┌──────────────────────────────────┐
│ auth-gateway validates request:  │
│ - Port not already in use        │
│ - Name not already registered    │
│ - Image is a valid reference     │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│ Insert into servers table        │
│ (source = 'dynamic')             │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│ Docker API: pull image, create   │
│ + start container on mcpfarm     │
│ network with MCP_TRANSPORT=      │
│ streamable-http, MCP_PORT=port   │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│ Regenerate Caddy routes.conf     │
│ (add new route block)            │
│ Signal Caddy to reload config    │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│ Health-check loop picks up new   │
│ server, marks healthy once /mcp/ │
│ responds                         │
└──────────────────────────────────┘
```

### 5.2 Implementation: Docker Socket

The auth-gateway container mounts the Docker socket (`/var/run/docker.sock`) to manage containers:

```yaml
auth-gateway:
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
    - auth_data:/data
```

It uses the Docker SDK for Python (`docker` package) to:
- Pull images
- Create and start containers on the `mcpfarm_internal` network
- Stop and remove containers
- Read container logs

### 5.3 Caddy Hot Reload

When a new server is registered or removed, the auth-gateway:
1. Regenerates `routes.conf` from the `servers` table
2. Writes it to a shared volume mounted by both auth-gateway and Caddy
3. Calls Caddy's admin API (`POST http://caddy:2019/load`) to reload, or sends SIGUSR1

### 5.4 Constraints

- Dynamically added servers are **not persisted in docker-compose.yml** — they exist only as running containers. If the farm is fully restarted (`docker compose down && up`), only static servers come back. Dynamic servers must be re-registered (or the admin API can re-create them from the `servers` table on startup).
- The auth-gateway's startup routine reads all `source='dynamic'` entries from SQLite and attempts to re-launch them, making dynamic servers survive gateway restarts.

---

## 6. Upstream API Keys (Transparent Pass-Through)

### 6.1 Design Principle

Some MCP servers require third-party API keys to function (Shodan for `uncover-mcp`, ProjectDiscovery for `cvemap-mcp`, OpenAI for `openrisk-mcp`, etc.). The farm does **not** store, manage, or broker these keys. From the user's perspective, configuring an MCP server in the farm is identical to configuring any standalone MCP server — they provide whatever keys the tool needs, alongside their Hackerdogs Bearer token. The farm is transparent infrastructure; it adds security, not complexity.

### 6.2 How It Works

Users pass upstream API keys as HTTP headers in their MCP client config. Caddy forwards these headers untouched to the MCP server container. A thin shared middleware inside each server extracts `X-*` headers from the incoming request and injects them as environment variables into the subprocess that runs the underlying CLI tool.

```
Client config                     Caddy                    MCP Server Container
┌──────────────────┐         ┌──────────────┐         ┌──────────────────────────┐
│ headers:         │         │              │         │ Middleware extracts:     │
│  Authorization:  │────────▶│  forward_auth│────────▶│  X-PDCP-API-KEY header  │
│    Bearer hd_sk_ │         │  (verify)    │         │       ↓                 │
│  X-PDCP-API-KEY: │         │  then proxy  │         │  env PDCP_API_KEY=...   │
│    pdcp_user123  │         │              │         │       ↓                 │
└──────────────────┘         └──────────────┘         │  cvemap subprocess      │
                                                      │  (reads env as normal)  │
                                                      └──────────────────────────┘
```

### 6.3 Client Config Example

The user's MCP client config looks like any other MCP server — the farm is invisible:

```json
{
  "mcpServers": {
    "cvemap-mcp": {
      "url": "https://mcp.hackerdogs.ai/cvemap-mcp/mcp/",
      "transport": "streamable-http",
      "headers": {
        "Authorization": "Bearer hd_sk_a1b2c3d4...",
        "X-PDCP-API-KEY": "pdcp_user_key_here"
      }
    },
    "uncover-mcp": {
      "url": "https://mcp.hackerdogs.ai/uncover-mcp/mcp/",
      "transport": "streamable-http",
      "headers": {
        "Authorization": "Bearer hd_sk_a1b2c3d4...",
        "X-SHODAN-API-KEY": "shodan_user_key_here",
        "X-CENSYS-API-TOKEN": "censys_user_token_here"
      }
    },
    "naabu-mcp": {
      "url": "https://mcp.hackerdogs.ai/naabu-mcp/mcp/",
      "transport": "streamable-http",
      "headers": {
        "Authorization": "Bearer hd_sk_a1b2c3d4..."
      }
    }
  }
}
```

Servers that don't require upstream keys (like `naabu-mcp`) only need the Bearer token. Servers that do (like `cvemap-mcp`) accept the keys as `X-` prefixed headers that map 1:1 to the environment variables documented in each server's README. No special "farm" configuration — just standard HTTP headers.

### 6.4 Header-to-Env Middleware

A shared Python module (`request_env.py`) is imported by every MCP server. It uses `contextvars` to provide per-request environment isolation — concurrent requests from different users with different API keys never interfere with each other.

```python
"""request_env.py — shared across all MCP servers in the farm."""
import os
from contextvars import ContextVar

_request_env: ContextVar[dict] = ContextVar("request_env", default={})

HEADER_TO_ENV = {
    "x-pdcp-api-key": "PDCP_API_KEY",
    "x-shodan-api-key": "SHODAN_API_KEY",
    "x-censys-api-token": "CENSYS_API_TOKEN",
    "x-openai-api-key": "OPENAI_API_KEY",
    "x-anthropic-api-key": "ANTHROPIC_API_KEY",
    # ... one entry per upstream key across all servers
}

def set_request_env(headers: dict):
    """Called by Starlette middleware on each incoming request."""
    overrides = {}
    for header, env_var in HEADER_TO_ENV.items():
        value = headers.get(header)
        if value:
            overrides[env_var] = value
    _request_env.set(overrides)

def get_subprocess_env() -> dict:
    """Called by tool functions when spawning CLI subprocesses."""
    env = os.environ.copy()
    env.update(_request_env.get())
    return env
```

Each server's `_run_command` changes one line:

```python
# Before (reads process-level env only):
proc = await asyncio.create_subprocess_exec(*cmd, ...)

# After (reads per-request env with user's upstream keys):
proc = await asyncio.create_subprocess_exec(*cmd, env=get_subprocess_env(), ...)
```

### 6.5 Why This Design

| Property | How it's achieved |
|----------|-------------------|
| **Transparent to users** | Config looks identical to any standalone MCP server; the farm adds no extra fields or concepts |
| **Farm stays stateless** | No upstream keys stored in SQLite or anywhere on the farm; keys live in the user's client config |
| **Per-request isolation** | `contextvars` ensures User A's Shodan key never leaks to User B's concurrent request |
| **Minimal server changes** | One shared module import + one line change in `_run_command` per server |
| **Graceful degradation** | If a user doesn't provide an upstream key, the server falls back to container-level env (from `.env`) or runs without it (with a warning, as servers already do today) |
| **No LLM exposure** | Keys are HTTP headers, not MCP tool arguments — the LLM never sees them in its context |

### 6.6 Fallback Chain

For any upstream API key, the resolution order is:

```
1. Per-request header (X-PDCP-API-KEY from user's client config)
       ↓ if not present
2. Container environment variable (PDCP_API_KEY from .env / docker-compose)
       ↓ if not present
3. None — server runs without it (warns, degrades, or errors as it does today)
```

This means the farm operator can set default keys in `.env` for shared/free-tier access, and individual users can override with their own keys for higher rate limits or premium access. Users who don't provide keys still get whatever the farm-level default offers.

### 6.7 Security Considerations

- **Keys in transit:** Upstream API keys travel through Cloudflare Tunnel (encrypted) and the internal Docker network. Caddy access logs must be configured to redact `X-*` headers containing keys.
- **Keys at rest:** Never stored on the farm. They exist only in the user's local MCP client config and in-memory for the duration of a single request.
- **Log redaction:** The auth-gateway's audit log records which server was called and by which API key, but never logs upstream API key values.

---

## 7. Port Allocation Strategy

With 155+ servers, ports are allocated systematically:

| Range | Category | Examples |
|-------|----------|----------|
| 8100–8119 | Core / Phase 1 tools | julius, augustus, naabu, cvemap |
| 8120–8149 | Network recon | rustscan, zmap, fping, arp-scan |
| 8150–8179 | Vulnerability scanning | trivy, grype, nikto, nuclei |
| 8180–8209 | Web application testing | dalfox, wfuzz, xsstrike, sqlmap |
| 8210–8239 | OSINT | sherlock, maigret, holehe, ghunt |
| 8240–8269 | Exploitation / Post-exploit | metasploit, hydra, john, hashcat |
| 8270–8299 | Cloud / Container security | kube-hunter, trivy, checkov, scout |
| 8300–8329 | Binary analysis / RE | ghidra, radare2, cutter, binwalk |
| 8330–8359 | Network attacks / Wireless | bettercap, ettercap, aircrack-ng |
| 8360–8399 | Misc / Overflow | remaining servers |
| 8400–8499 | **Reserved for dynamic servers** | added via admin API at runtime |

A canonical `port-map.json` file maps server names to ports, used by:
- The docker-compose generator script
- Caddy configuration
- Auth gateway service registry (pre-seeded on first boot)

---

## 8. Deployment & Configuration

### 8.1 Directory Structure

```
mcpfarm/
├── docker-compose.yml          # Generated — all 155+ services + infra
├── docker-compose.override.yml # Local overrides (API keys, dev settings)
├── .env                        # Environment variables (API keys, secrets)
├── .env.example                # Template
├── port-map.json               # Canonical server→port mapping
│
├── caddy/
│   ├── Caddyfile               # Reverse proxy config
│   └── routes.conf             # Auto-generated per-server routes
│
├── auth-gateway/
│   ├── Dockerfile
│   ├── main.py                 # FastAPI — all admin + auth logic
│   ├── models.py               # SQLite models
│   ├── docker_manager.py       # Docker SDK wrapper for dynamic servers
│   ├── caddy_reload.py         # Caddy route generation + reload
│   ├── requirements.txt
│   └── seed.py                 # Bootstrap: seed static servers + first admin key
│
├── cloudflared/
│   └── (uses TUNNEL_TOKEN env — no config files needed)
│
└── scripts/
    ├── generate-compose.py     # Build the master compose file from port-map.json
    └── health-check.sh         # CLI health check for all servers
```

### 8.2 Environment Variables (`.env`)

```bash
# ── Cloudflare Tunnel ──
TUNNEL_TOKEN=<cloudflare-tunnel-token>

# ── Auth Gateway ──
ADMIN_SECRET=<random-admin-secret>
AUTH_DB_PATH=/data/auth.db

# ── API Keys for upstream services (optional) ──
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
PDCP_API_KEY=
SHODAN_API_KEY=
CENSYS_API_TOKEN=
# ... (all optional, servers degrade gracefully without them)
```

### 8.3 Launch Sequence

```bash
# 1. Clone the repo
git clone https://github.com/hackerdogs/hd-mcpservers-docker.git
cd hd-mcpservers-docker/mcpfarm

# 2. Configure environment
cp .env.example .env
# Edit .env with your TUNNEL_TOKEN, ADMIN_SECRET, and any upstream API keys

# 3. Generate the master compose file (if not already committed)
python scripts/generate-compose.py

# 4. Pull all pre-built images and launch
docker compose pull && docker compose up -d

# 5. Seed the first admin API key (one-time, on first boot)
docker compose exec auth-gateway python seed.py
# Prints: Admin key: hd_sk_...

# 6. Create user API keys via the admin API
curl -X POST http://localhost:9090/admin/keys \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-agent", "scopes": "*"}'

# 7. Dynamically add a new server (no restart needed)
curl -X POST http://localhost:9090/admin/servers \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-new-mcp", "image": "hackerdogs/my-new-mcp:latest", "port": 8400}'
```

### 8.4 Client Configuration

An MCP client (Claude Desktop, Cursor, OpenAI Agents, etc.) connects like this:

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
    "trivy": {
      "url": "https://mcp.hackerdogs.ai/trivy-mcp/mcp/",
      "transport": "streamable-http",
      "headers": {
        "Authorization": "Bearer hd_sk_a1b2c3d4..."
      }
    }
  }
}
```

---

## 9. Architecture Decisions

### 9.1 Dynamic Routing in Caddy

**Problem:** 155+ servers each on a different internal port. Hard-coding 155 `reverse_proxy` blocks is fragile.

**Chosen approach: Caddy with auto-generated route file + hot reload**

A `generate-compose.py` script produces both `docker-compose.yml` and `caddy/routes.conf` from `port-map.json`. At runtime, the auth-gateway regenerates `routes.conf` when dynamic servers are added/removed and signals Caddy to reload.

```caddyfile
# routes.conf (auto-generated, never hand-edited)
@julius-mcp path /julius-mcp/*
handle @julius-mcp {
    forward_auth auth-gateway:9090 {
        uri /verify
        copy_headers Authorization
    }
    uri strip_prefix /julius-mcp
    reverse_proxy julius-mcp:8100
}

@naabu-mcp path /naabu-mcp/*
handle @naabu-mcp {
    forward_auth auth-gateway:9090 {
        uri /verify
        copy_headers Authorization
    }
    uri strip_prefix /naabu-mcp
    reverse_proxy naabu-mcp:8105
}
# ... 153+ more (auto-generated)
```

### 9.2 API-Only Admin (No UI)

**Why no UI:**

| Factor | API-only | Web dashboard |
|--------|----------|---------------|
| Attack surface | Minimal — one FastAPI service | Additional frontend, auth cookies, CSRF, XSS vectors |
| Automation | Trivially scriptable with `curl` / any HTTP client | Requires browser automation or duplicate API |
| Maintenance | Zero frontend dependencies | Node.js/React build, ongoing dependency updates |
| Security audit | Single codebase to audit | Two codebases (API + frontend) |
| Target users | DevOps engineers, scripts, other agents | General users (not our audience) |

Every management operation is a `curl` command. The farm is designed to be managed by automation — CI/CD, Ansible playbooks, or other LLM agents calling the admin API.

### 9.3 Auth at Caddy vs. Auth at Each Server

**Chosen: Auth at Caddy (forward_auth)**

| Approach | Pros | Cons |
|----------|------|------|
| Caddy forward_auth | Single auth point, servers remain unmodified, easy to audit | Extra hop per request |
| Per-server middleware | No extra service | Must modify 155+ servers, inconsistent enforcement |
| Cloudflare Access | Zero-trust, no self-managed auth | Vendor lock-in, per-seat pricing, less flexible for API keys |

### 9.4 SQLite for Token Storage

**Why SQLite over Postgres/Redis:**

- **Self-contained:** No additional database service to manage
- **Performance:** WAL mode handles thousands of concurrent reads; token verification is a single indexed lookup (~0.01ms)
- **Durability:** Single file, easy to backup via volume mount
- **Scalability path:** If the farm grows beyond a single node, migrate to Turso (distributed SQLite) or Postgres with zero code changes

**Scaling strategy:**

```
Phase 1 (current):  SQLite WAL on local volume
Phase 2 (multi-node): Turso/LiteFS for distributed SQLite
Phase 3 (enterprise):  Postgres + Redis cache for sub-ms lookups
```

### 9.5 Stateless & Isolated Design

| Property | How it's achieved |
|----------|-------------------|
| **Stateless MCP servers** | No volumes, no persistent data; tool results are computed and returned immediately |
| **Isolated** | Each server in its own container, own network namespace, non-root user, read-only filesystem possible |
| **Self-contained** | All 155+ servers + infra in one compose file; no external services required |
| **Reproducible** | Pre-built images pinned to `latest` (or SHA tags for production); `port-map.json` is the single source of truth |

---

## 10. Security Model

### 10.1 Network Isolation

```
Internet ──▶ Cloudflare ──▶ cloudflared ──▶ Caddy ──▶ MCP servers
                                               │
                                               ├── auth-gateway (internal only)
                                               └── MCP servers (internal only)
```

- **No host ports exposed** for MCP servers (only Caddy port 80 is on the Docker bridge, and even that is only accessed by cloudflared within the same network)
- **Internal Docker network** (`mcpfarm_internal`) isolates all containers
- **cloudflared** establishes outbound-only tunnel — no inbound firewall rules needed

### 10.2 Authentication Flow

```
Client Request
    │
    ▼
┌─────────────────────────┐
│ Has Authorization header?│
│         Bearer token?    │
└──────────┬──────────────┘
           │ No → 401 Unauthorized
           │ Yes
           ▼
┌─────────────────────────┐
│ SHA-256(token) lookup    │
│ in api_keys table        │
└──────────┬──────────────┘
           │ Not found → 401
           │ Found
           ▼
┌─────────────────────────┐
│ is_active = true?        │
│ expires_at > now?        │
│ scopes include server?   │
│ rate_limit not exceeded?  │
└──────────┬──────────────┘
           │ Any fail → 403 Forbidden
           │ All pass
           ▼
┌─────────────────────────┐
│ Update last_used, log    │
│ Forward to MCP server    │
└─────────────────────────┘
```

### 10.3 Rate Limiting

Per-key rate limiting using a sliding window counter stored in-memory (no Redis needed for single-node):

```python
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self):
        self.windows = defaultdict(list)

    def check(self, key_id: str, limit: int, window_seconds: int = 60) -> bool:
        now = time.time()
        cutoff = now - window_seconds
        self.windows[key_id] = [t for t in self.windows[key_id] if t > cutoff]
        if len(self.windows[key_id]) >= limit:
            return False
        self.windows[key_id].append(now)
        return True
```

### 10.4 Key Rotation

- Keys can be deactivated instantly via `PATCH /admin/keys/{id}` (set `is_active = false`)
- New keys created with `POST /admin/keys`
- Scoped keys restrict access to specific servers (e.g., `scopes: "naabu-mcp,trivy-mcp"`)
- Expired keys are automatically rejected (checked on every request)

---

## 11. Observability

### 11.1 Health Monitoring

**Caddy health endpoint:** `GET /health` returns 200 OK.

**Per-server health:** The auth-gateway periodically (every 30s) pings each MCP server's `/mcp/` endpoint and maintains a health registry. Exposed at `GET /services`:

```json
{
  "servers": [
    {
      "name": "naabu-mcp",
      "url": "/naabu-mcp/mcp/",
      "port": 8105,
      "source": "static",
      "status": "healthy",
      "last_check": "2026-03-14T12:00:00Z"
    },
    {
      "name": "my-custom-mcp",
      "url": "/my-custom-mcp/mcp/",
      "port": 8400,
      "source": "dynamic",
      "status": "healthy",
      "last_check": "2026-03-14T12:00:05Z"
    }
  ],
  "total": 157,
  "healthy": 155,
  "unhealthy": 2
}
```

### 11.2 Logging

- **Caddy:** Structured JSON access logs to stdout (Docker captures)
- **Auth gateway:** Request log table in SQLite for audit trail; structured logs to stdout
- **MCP servers:** stdout/stderr captured by Docker log driver
- **Aggregation:** Docker log driver can forward to any log sink (Loki, CloudWatch, etc.)
- **Audit queries:** `GET /admin/audit?server=naabu-mcp&since=2026-03-14T00:00:00Z&limit=100`

### 11.3 Metrics (Future)

- Prometheus metrics from auth-gateway (`/metrics`)
- Per-server request count, latency p50/p95/p99
- Per-key usage tracking

---

## 12. LLM Safety Guardrails — Tool-Call Firewall

### 12.1 The Problem

MCP servers execute real security tools — port scanners, exploit frameworks, brute-force utilities. An LLM (or an LLM under prompt injection) could:

- Invoke destructive tools against unintended targets
- Chain tools in dangerous sequences (recon → exploit → exfiltrate)
- Exfiltrate data through tool arguments or return values
- Bypass intended scope by crafting creative tool call arguments
- Execute denial-of-service attacks via high-volume scanning

A guardrail layer between the LLM/agent and the MCP servers can intercept, inspect, and block dangerous tool invocations before they reach the security tools.

### 12.2 Design Principle: Invisible Security

The guardrail is **always on and invisible to the user**. Users don't "enable" a firewall, don't configure policies, and don't see a different protocol. They connect to a standard MCP endpoint and their requests are silently inspected. If a request is blocked, the user receives a standard MCP error response — no special error format, no firewall-specific headers. The guard is infrastructure, not a feature users interact with.

### 12.3 Where the Guard Sits

```
LLM/Agent → [Tool-Call Guard] → Caddy → auth-gateway → MCP Server
```

The guard is deployed as an **inline container in the farm's Docker network** — sitting between Caddy and the MCP servers, or as a sidecar MCP proxy between the client and Caddy. Either way, it is:

1. **Invisible to the client** — no config changes, no extra endpoints, no awareness required
2. **Invisible to the MCP server** — the server sees a normal request, unaware of the guard
3. **Always on** — not opt-in, not per-key, not configurable by users
4. **Farm-operator controlled** — policies are set by the farm admin via YAML files or the admin API, never by end users

### 12.4 Open-Source Options

Below are **8 open-source, free, self-hostable** guardrail and firewall tools evaluated for this use case. They are grouped by approach.

---

#### Category A: MCP-Native Tool-Call Firewalls

These operate directly at the MCP protocol layer — they understand `tools/call` requests and can block, modify, or rate-limit them.

**1. PolicyLayer Intercept**

| Attribute | Detail |
|-----------|--------|
| **Repo** | [github.com/policylayer/intercept](https://github.com/policylayer/intercept) |
| **License** | Apache 2.0 |
| **Language** | Go |
| **Approach** | Transparent MCP proxy with YAML policy enforcement |
| **Latency** | Sub-millisecond (deterministic, no ML) |
| **Key features** | Default-deny mode, tool hiding (strip from discovery), argument validation via regex, per-tool rate limiting, spend tracking, hot-reload policies without restart |
| **MCP-aware** | Yes — intercepts `tools/list` and `tools/call` at the protocol level |
| **How it fits** | Deploy as a sidecar container in the farm. Clients connect to Intercept, which proxies to the actual MCP servers through Caddy. YAML policies define allowed tools, argument constraints, and rate limits per server. |
| **Example policy** | `deny tools matching "metasploit*" unless argument "target" matches internal CIDR` |
| **Verdict** | **Best fit for the farm.** MCP-native, zero ML overhead, policy-as-code, Apache 2.0. |

**2. AvaKill**

| Attribute | Detail |
|-----------|--------|
| **Repo** | [github.com/log-bell/avakill](https://github.com/log-bell/avakill) |
| **License** | AGPL-3.0 |
| **Language** | Python |
| **Approach** | Deterministic safety firewall with YAML policy enforcement + MCP proxy mode |
| **Latency** | < 1ms (no ML, no API calls) |
| **Key features** | 81 pre-built rules across 14 categories, MCP proxy for transparent protection, OS-level sandboxing (Landlock/sandbox-exec/AppContainer), agent hooks for Claude Code/Cursor/Windsurf |
| **MCP-aware** | Yes — has dedicated MCP proxy mode |
| **How it fits** | Can run as an MCP proxy container intercepting all traffic, or hook directly into agent runtimes. Pre-built rules cover file deletion, network exfiltration, privilege escalation. |
| **Caveat** | AGPL-3.0 license — any modifications must be open-sourced. Fine for internal use, but check compliance if distributing. |
| **Verdict** | **Strong option.** Mature rule catalog, MCP-native, but AGPL license is more restrictive. |

**3. ressl/mcp-firewall**

| Attribute | Detail |
|-----------|--------|
| **Repo** | [github.com/ressl/mcp-firewall](https://github.com/ressl/mcp-firewall) |
| **License** | AGPL-3.0 |
| **Language** | Python |
| **Approach** | Enterprise-grade MCP security gateway |
| **Key features** | 8 inbound + 4 outbound security checks, policy-as-code (YAML + OPA/Rego), cryptographically signed audit trails, compliance reporting (DORA, FINMA, SOC 2) |
| **MCP-aware** | Yes |
| **How it fits** | Heavy-duty option if compliance/audit trails matter. OPA/Rego policies are very expressive for complex rules. |
| **Caveat** | AGPL-3.0. More enterprise-oriented — may be over-engineered for initial deployment. |
| **Verdict** | **Best for compliance-heavy environments.** Overkill for v1 but good graduation path. |

**4. mcpwall (behrensd)**

| Attribute | Detail |
|-----------|--------|
| **Repo** | [github.com/behrensd/mcp-firewall](https://github.com/behrensd/mcp-firewall) |
| **License** | Apache 2.0 |
| **Language** | TypeScript |
| **Approach** | "iptables for MCP" — deterministic proxy |
| **Key features** | YAML policies, secret leakage scanning, full audit logging, zero-cloud, works with Claude Code/Cursor/Windsurf |
| **MCP-aware** | Yes |
| **How it fits** | Lightweight alternative to PolicyLayer Intercept. TypeScript makes it easy to extend. |
| **Verdict** | **Good lightweight option.** Apache 2.0, simple policy model. |

---

#### Category B: LLM Agent Safety Frameworks

These are broader frameworks that guard LLM behavior including but not limited to tool calls. They can catch prompt injection, goal misalignment, and reasoning-chain attacks.

**5. IronCurtain**

| Attribute | Detail |
|-----------|--------|
| **Repo** | [github.com/provos/ironcurtain](https://github.com/provos/ironcurtain) |
| **License** | Apache 2.0 |
| **Language** | TypeScript |
| **Approach** | MCP proxy with constitution-based policy enforcement |
| **Key features** | Plain-English "constitution" compiled into deterministic security rules, V8 sandbox for agent code, MCP server sandboxing with minimum permissions, automatic approval system, complete audit logging |
| **MCP-aware** | Yes — designed specifically as an MCP proxy |
| **How it fits** | Unique approach: you write safety rules in natural language ("never scan targets outside the 10.0.0.0/8 range"), and IronCurtain compiles them into enforceable structural invariants. The constitution is compiled once — no LLM calls at runtime. |
| **Caveat** | Newer project (v0.7.2, Feb 2026). Constitution compilation requires a one-time LLM call. |
| **Verdict** | **Most innovative approach.** Natural-language policies are powerful for security teams who think in terms of rules, not code. |

**6. LlamaFirewall (Meta)**

| Attribute | Detail |
|-----------|--------|
| **Repo** | [github.com/meta-llama/PurpleLlama](https://github.com/meta-llama/PurpleLlama) (under LlamaFirewall/) |
| **License** | MIT |
| **Language** | Python |
| **Approach** | ML-based multi-scanner pipeline for prompt injection, jailbreak, code safety, and agent alignment |
| **Latency** | ~100ms+ (runs ML models) |
| **Key features** | PromptGuard 2 (jailbreak/injection detector), Agent Alignment Checks (chain-of-thought auditor), CodeShield (static analysis), custom regex/LLM scanners |
| **MCP-aware** | No — operates on text inputs/outputs, not MCP protocol |
| **How it fits** | Deploy as a pre-processing layer that scans LLM outputs before they become MCP tool calls. Catches prompt injection and reasoning-chain manipulation that deterministic rules might miss. Can complement a MCP-native firewall. |
| **Caveat** | Requires GPU for optimal performance (CPU inference is slower). Adds ~100ms+ latency per scan. |
| **Verdict** | **Best ML-based detection.** Use alongside a deterministic MCP firewall for defense-in-depth. |

**7. NeMo Guardrails (NVIDIA)**

| Attribute | Detail |
|-----------|--------|
| **Repo** | [github.com/nvidia/nemo-guardrails](https://github.com/nvidia/nemo-guardrails) |
| **License** | Apache 2.0 |
| **Language** | Python |
| **Approach** | Programmable conversational guardrails using Colang DSL |
| **Latency** | ~200ms+ |
| **Key features** | Custom DSL (Colang) for defining safety flows, topic control, PII detection, jailbreak prevention, hallucination checks, integrates with LangChain/LlamaIndex |
| **MCP-aware** | Partial — supports tool integration but not MCP-protocol-native |
| **How it fits** | Best used at the agent orchestration layer (e.g., inside a LangChain agent) rather than as a network proxy. Defines conversation-level safety rails ("if user asks to scan, verify target is authorized first"). |
| **Caveat** | Steeper learning curve (Colang DSL). Higher latency. Designed for conversational apps more than tool-call firewalls. |
| **Verdict** | **Best for conversation-level safety.** Good if the agent layer is custom-built with LangChain. |

---

#### Category C: LLM Inference Proxies

These sit between the application and the LLM provider, scanning inputs and outputs for threats. Complementary to MCP-layer firewalls.

**8. InferShield**

| Attribute | Detail |
|-----------|--------|
| **Repo** | [github.com/InferShield/infershield](https://github.com/InferShield/infershield) |
| **License** | MIT |
| **Language** | JavaScript/Python |
| **Approach** | Reverse proxy between app and LLM API providers |
| **Key features** | Prompt injection detection, multi-encoding attack detection (base64/hex/URL/Unicode), PII leakage prevention, SQL injection catching, session-aware threat detection, zero code changes (drop-in proxy) |
| **MCP-aware** | No — operates at the LLM API layer, not MCP |
| **How it fits** | Deploy between the agent and its LLM provider. Catches malicious prompts before they reach the LLM that would then generate dangerous tool calls. First line of defense. |
| **Docker support** | Yes — `docker pull infershield/infershield` |
| **Verdict** | **Best for LLM-layer defense.** Complementary to MCP-layer firewalls. |

---

### 12.5 Recommended Architecture: Defense-in-Depth

No single tool covers all threat vectors. The recommended approach layers multiple guards:

```
┌─────────────────────────────────────────────────────────────────┐
│                        DEFENSE LAYERS                           │
│                                                                 │
│  Layer 1: LLM Input/Output Guard                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  InferShield (MIT) — proxy between agent and LLM API   │    │
│  │  Catches: prompt injection, jailbreak, PII leakage     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                     │
│  Layer 2: Agent Reasoning Guard                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  LlamaFirewall (MIT) — scans LLM output before         │    │
│  │  tool calls are made                                    │    │
│  │  Catches: goal misalignment, chain-of-thought attacks   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                     │
│  Layer 3: MCP Tool-Call Firewall (THE CRITICAL LAYER)           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  PolicyLayer Intercept (Apache 2.0) — MCP proxy        │    │
│  │  Catches: unauthorized tools, dangerous arguments,     │    │
│  │  rate abuse, scope violations                           │    │
│  │  Enforcement: deterministic, <1ms, policy-as-code      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                     │
│  Layer 4: Network + Auth                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Caddy + auth-gateway — Bearer token, scopes, rate     │    │
│  │  limits, network isolation                              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                     │
│                    MCP Server Farm                               │
└─────────────────────────────────────────────────────────────────┘
```

### 12.6 Comparison Matrix

| Tool | License | MCP-Native | ML Required | Latency | Approach | Best For |
|------|---------|------------|-------------|---------|----------|----------|
| **PolicyLayer Intercept** | Apache 2.0 | Yes | No | <1ms | YAML policies | Tool-call firewall (primary) |
| **AvaKill** | AGPL-3.0 | Yes | No | <1ms | YAML + OS sandbox | Tool-call firewall + host protection |
| **mcpwall** | Apache 2.0 | Yes | No | <1ms | YAML policies | Lightweight tool-call firewall |
| **ressl/mcp-firewall** | AGPL-3.0 | Yes | No | Low | YAML + OPA/Rego | Compliance-heavy environments |
| **IronCurtain** | Apache 2.0 | Yes | No (one-time compile) | <1ms | Natural-language constitution | Teams who prefer English over YAML |
| **LlamaFirewall** | MIT | No | Yes (models) | ~100ms | ML classifiers | Prompt injection + alignment detection |
| **NeMo Guardrails** | Apache 2.0 | Partial | Optional | ~200ms | Colang DSL | Conversation-level safety |
| **InferShield** | MIT | No | Heuristic | Low | Reverse proxy | LLM API input/output scanning |

### 12.7 Recommended Starting Configuration

For the MCP Server Farm v1, start with **two layers**:

1. **PolicyLayer Intercept** (Apache 2.0) as the MCP tool-call firewall
   - Deploy as a container in the compose stack
   - All MCP traffic routes through it before reaching the actual MCP servers
   - YAML policies define allowed tools, argument validation, rate limits
   - Zero ML, sub-millisecond, deterministic

2. **LlamaFirewall** (MIT) as the agent-side reasoning guard
   - Optional — deployed by the agent operator, not the farm
   - Scans LLM outputs before tool calls are dispatched
   - Catches prompt injection that deterministic rules miss

**Phase 2 additions:**
- IronCurtain for natural-language constitution-based policies
- InferShield if the farm also proxies LLM API calls

---

## 13. Docker Compose Structure

The master `docker-compose.yml` follows this pattern:

```yaml
services:
  # ── Infrastructure ──
  caddy:
    image: caddy:2-alpine
    container_name: mcpfarm-caddy
    volumes:
      - ./caddy/Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_routes:/etc/caddy/dynamic:ro
    networks:
      - mcpfarm
    depends_on:
      auth-gateway:
        condition: service_healthy
    restart: unless-stopped

  auth-gateway:
    build: ./auth-gateway
    container_name: mcpfarm-auth
    environment:
      - ADMIN_SECRET=${ADMIN_SECRET}
      - AUTH_DB_PATH=/data/auth.db
    volumes:
      - auth_data:/data
      - caddy_routes:/caddy-routes
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - mcpfarm
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9090/health"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped

  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: mcpfarm-tunnel
    command: tunnel run
    environment:
      - TUNNEL_TOKEN=${TUNNEL_TOKEN}
    networks:
      - mcpfarm
    depends_on:
      - caddy
    restart: unless-stopped

  # ── MCP Servers (155+ entries, auto-generated) ──
  julius-mcp:
    image: hackerdogs/julius-mcp:latest
    container_name: julius-mcp
    environment:
      - MCP_TRANSPORT=streamable-http
      - MCP_PORT=8100
    networks:
      - mcpfarm
    restart: unless-stopped

  naabu-mcp:
    image: hackerdogs/naabu-mcp:latest
    container_name: naabu-mcp
    environment:
      - MCP_TRANSPORT=streamable-http
      - MCP_PORT=8105
    networks:
      - mcpfarm
    restart: unless-stopped

  # ... 153 more servers (auto-generated from port-map.json) ...

networks:
  mcpfarm:
    driver: bridge
    name: mcpfarm_internal

volumes:
  auth_data:
    name: mcpfarm_auth_data
  caddy_routes:
    name: mcpfarm_caddy_routes
```

**Key differences from current compose:**
- No `ports:` on MCP servers — only reachable via internal network
- Auth-gateway mounts Docker socket for dynamic server management
- Shared `caddy_routes` volume for hot-reloading Caddy config
- No UI containers — everything is API-driven

---

## 14. Compose Generator Script

Because maintaining 155+ service entries by hand is error-prone, a Python script generates both the compose file and Caddy routes from `port-map.json`:

**`port-map.json` (source of truth):**

```json
{
  "julius-mcp": { "port": 8100 },
  "augustus-mcp": { "port": 8101, "env": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"] },
  "naabu-mcp": { "port": 8105 },
  "cvemap-mcp": { "port": 8106, "env": ["PDCP_API_KEY"] },
  "trivy-mcp": { "port": 8150 },
  "...": "..."
}
```

**`generate-compose.py`** reads `port-map.json` and outputs:
1. `docker-compose.yml` with all services (infra + MCP servers)
2. `caddy/routes.conf` with all route matchers
3. Validates no port collisions
4. Seeds the `servers` table in the auth-gateway database

---

## 15. Resource Requirements

### 15.1 Per-Server Footprint

| Resource | Idle | Active |
|----------|------|--------|
| Memory | 30–80 MB | 100–500 MB (tool-dependent) |
| CPU | ~0% | Burst during tool execution |
| Disk | 0 (stateless) | Temp files cleaned per-request |

### 15.2 Farm Totals (155 servers)

| Resource | Estimate |
|----------|----------|
| Memory (idle) | ~8–12 GB |
| Memory (10 concurrent) | ~12–16 GB |
| Disk (images) | ~40–60 GB |
| CPU | 4+ cores recommended |

### 15.3 Recommended Host

| Tier | Spec | Servers |
|------|------|---------|
| Dev/Test | 16 GB RAM, 4 CPU, 100 GB SSD | ~50 servers |
| Production | 32 GB RAM, 8 CPU, 200 GB SSD | All 155+ servers |
| High-load | 64 GB RAM, 16 CPU, 500 GB SSD | All servers + headroom |

---

## 16. Operational Runbook

### 16.1 Common Operations (All via API)

```bash
# ── Farm Lifecycle ──
docker compose up -d                    # Start the entire farm
docker compose down                     # Stop the entire farm
docker compose pull && docker compose up -d  # Update all images

# ── API Key Management ──
# Create a key
curl -X POST https://mcp.hackerdogs.ai/admin/keys \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-agent", "scopes": "*"}'

# List all keys
curl https://mcp.hackerdogs.ai/admin/keys \
  -H "X-Admin-Secret: $ADMIN_SECRET"

# Revoke a key
curl -X DELETE https://mcp.hackerdogs.ai/admin/keys/{id} \
  -H "X-Admin-Secret: $ADMIN_SECRET"

# ── Dynamic Server Management ──
# Add a new server (no compose restart)
curl -X POST https://mcp.hackerdogs.ai/admin/servers \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-scanner-mcp", "image": "hackerdogs/my-scanner-mcp:latest", "port": 8401}'

# Remove a dynamic server
curl -X DELETE https://mcp.hackerdogs.ai/admin/servers/my-scanner-mcp \
  -H "X-Admin-Secret: $ADMIN_SECRET"

# Restart a server
curl -X POST https://mcp.hackerdogs.ai/admin/servers/naabu-mcp/restart \
  -H "X-Admin-Secret: $ADMIN_SECRET"

# Get server logs
curl https://mcp.hackerdogs.ai/admin/servers/naabu-mcp/logs?lines=100 \
  -H "X-Admin-Secret: $ADMIN_SECRET"

# ── Monitoring ──
# Farm health
curl https://mcp.hackerdogs.ai/health

# All servers with health status
curl https://mcp.hackerdogs.ai/services

# Farm stats
curl https://mcp.hackerdogs.ai/admin/stats \
  -H "X-Admin-Secret: $ADMIN_SECRET"

# Audit log query
curl "https://mcp.hackerdogs.ai/admin/audit?server=naabu-mcp&since=2026-03-14&limit=50" \
  -H "X-Admin-Secret: $ADMIN_SECRET"
```

### 16.2 Disaster Recovery

- **Auth DB backup:** `curl -X POST https://mcp.hackerdogs.ai/admin/backup -H "X-Admin-Secret: $ADMIN_SECRET" > auth-backup.db`
- **Full farm restore:** `docker compose pull && docker compose up -d` (stateless servers need no restore; dynamic servers auto-recreated from SQLite)
- **Tunnel recovery:** cloudflared auto-reconnects; if persistent, recreate tunnel in Cloudflare dashboard

---

## 17. Future Enhancements

| Enhancement | Description | Priority |
|-------------|-------------|----------|
| **Server profiles** | Deploy subsets (e.g., "recon-only", "vuln-scan-only") via compose profiles | High |
| **Tool-call firewall** | Deploy PolicyLayer Intercept as inline MCP proxy | High |
| **Auto-scaling** | Spin up additional container replicas for hot servers | Medium |
| **Distributed SQLite** | Turso/LiteFS for multi-node auth | Medium |
| **MCP Gateway protocol** | Single MCP endpoint that multiplexes to all servers | Low |
| **Warm-start pool** | Keep N spare containers pre-warmed for cold-start-heavy servers | Low |
| **RBAC** | Role-based access control beyond simple scopes | Low |

---

## 18. Success Criteria

| Criteria | Target |
|----------|--------|
| Time from `docker compose up` to all servers healthy | < 120 seconds (pre-pulled images) |
| Time from `docker compose pull && up` to ready | < 10 minutes (first deploy) |
| Auth overhead per request | < 5ms |
| Concurrent MCP sessions supported | 100+ |
| Zero-downtime server updates | Rolling restart via API |
| Mean time to add new MCP server via API | < 30 seconds (pull + start + route) |
| Dynamic server available after API call | < 60 seconds |
| **User transparency** | Client config is indistinguishable from any standalone MCP server config |
| **Upstream key pass-through latency** | < 1ms added by header-to-env middleware |
| **Guardrail transparency** | Blocked requests return standard MCP error — no firewall-specific protocol |

---

## 19. Open Questions

1. **Selective deployment:** Should we support deploying only a subset of servers via Docker Compose profiles (e.g., `--profile recon`, `--profile vuln`)?
2. **Cloudflare Access:** Should we add Cloudflare Access as a second auth layer in front of the tunnel, or is Bearer token auth sufficient?
3. ~~**Per-server API keys:**~~ **RESOLVED.** Upstream API keys are passed by the user as `X-*` HTTP headers in their client config — identical to how they'd configure any standalone MCP server. The farm is transparent; it passes keys through to the server container via a header-to-env middleware. Farm-level defaults in `.env` serve as fallback. See Section 6.
4. **WebSocket/SSE support:** Some future MCP transports may use WebSocket. Does Caddy + cloudflared handle long-lived connections correctly?
5. **Container resource limits:** Should we enforce per-container memory/CPU limits to prevent a runaway tool from starving the farm?
6. ~~**Guardrail deployment:**~~ **RESOLVED.** The tool-call firewall is always on, invisible to users, controlled by the farm operator. Users never opt in or out — the guardrail is infrastructure, not a feature. See Section 12.2.
7. **Dynamic server image trust:** Should dynamically-added servers be restricted to images from `hackerdogs/*` namespace, or allow arbitrary Docker Hub images?
