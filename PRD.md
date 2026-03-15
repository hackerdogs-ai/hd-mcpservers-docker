# PRD: Hackerdogs MCP Server Farm

## 1. Overview

A self-contained, stateless, isolated deployment of **155+ MCP (Model Context Protocol) security tool servers** behind a single Caddy reverse proxy, exposed to the internet via Cloudflare Tunnel at `mcp.hackerdogs.ai`, authenticated via API Key Bearer tokens stored in SQLite. The entire farm launches with a single `docker compose up` command and is ready for any MCP client or LLM to access over HTTP in seconds.

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

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DOCKER COMPOSE NETWORK                             │
│                            (mcpfarm_internal, bridge)                           │
│                                                                                 │
│  ┌──────────────┐    ┌───────────────┐    ┌────────────────┐                    │
│  │              │    │               │    │                │                    │
│  │  cloudflared │───▶│    Caddy      │───▶│  auth-gateway  │                    │
│  │  (tunnel)    │    │  (reverse     │    │  (token        │                    │
│  │              │    │   proxy)      │    │   validation)  │                    │
│  └──────────────┘    │               │    │                │                    │
│                      │  :443 / :80   │    │  :9090         │                    │
│                      └───────┬───────┘    └────────────────┘                    │
│                              │                                                  │
│            ┌─────────────────┼──────────────────┐                               │
│            │                 │                   │                               │
│            ▼                 ▼                   ▼                               │
│  ┌─────────────────┐ ┌──────────────┐ ┌─────────────────┐                       │
│  │  julius-mcp     │ │ naabu-mcp    │ │ trivy-mcp       │  ... 155+ servers    │
│  │  :8100          │ │ :8105        │ │ :8150           │                       │
│  └─────────────────┘ └──────────────┘ └─────────────────┘                       │
│                                                                                 │
│  ┌──────────────────────────────────────┐                                       │
│  │  SQLite DB (volume: auth_data)       │                                       │
│  │  /data/auth.db                       │                                       │
│  └──────────────────────────────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────────────┘
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

**Role:** Single ingress point for all MCP traffic. Handles TLS (local), routing, and delegates authentication.

**Why Caddy:**
- Automatic HTTPS with internal certificates
- Native `forward_auth` directive (no Lua/plugins needed)
- Simple, declarative Caddyfile configuration
- Wildcard path matching for 155+ services without manual per-service config

**Caddyfile Design (dynamic routing):**

```caddyfile
{
    admin off
    auto_https off
}

:80 {
    # Health check for Cloudflare tunnel
    handle /health {
        respond "OK" 200
    }

    # Service discovery endpoint (no auth)
    handle /services {
        reverse_proxy auth-gateway:9090
    }

    # All MCP server routes
    handle_path /{service}/* {
        forward_auth auth-gateway:9090 {
            uri /verify
            copy_headers {
                Authorization
                X-Forwarded-For
            }
        }
        reverse_proxy {service}:{service_port}
    }
}
```

> **Note:** Because each MCP server has a different internal port, Caddy needs a dynamic mapping. Two approaches are detailed in Section 7 (Architecture Decisions).

### 4.2 Auth Gateway

A lightweight Python (FastAPI) or Go microservice responsible for:

1. **Token validation** — `GET /verify` checks the `Authorization: Bearer <token>` header against SQLite
2. **Service registry** — `GET /services` returns a list of all available MCP servers and their health status
3. **Admin API** — CRUD operations for API keys (protected by admin secret)

**Database schema (SQLite with WAL):**

```sql
CREATE TABLE api_keys (
    id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    key_hash    TEXT NOT NULL UNIQUE,      -- SHA-256 hash of the API key
    key_prefix  TEXT NOT NULL,             -- First 8 chars for identification (e.g., "hd_sk_ab")
    name        TEXT NOT NULL,             -- Human-readable label
    owner       TEXT,                      -- Owner email or identifier
    scopes      TEXT DEFAULT '*',          -- Comma-separated server names, or '*' for all
    rate_limit  INTEGER DEFAULT 100,       -- Requests per minute
    is_active   BOOLEAN DEFAULT 1,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at  DATETIME,                  -- NULL = never expires
    last_used   DATETIME
);

CREATE INDEX idx_key_hash ON api_keys(key_hash);
CREATE INDEX idx_active ON api_keys(is_active);

CREATE TABLE request_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id      TEXT REFERENCES api_keys(id),
    server      TEXT NOT NULL,             -- Which MCP server was accessed
    method      TEXT,
    status      INTEGER,
    latency_ms  INTEGER,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_request_log_key ON request_log(key_id, created_at);
CREATE INDEX idx_request_log_time ON request_log(created_at);
```

**API Key format:** `hd_sk_<32 random hex chars>` (e.g., `hd_sk_a1b2c3d4e5f6...`)

**Admin API endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/admin/keys` | Create new API key (returns key once, stores hash) |
| `GET` | `/admin/keys` | List all keys (shows prefix, name, scopes, active status) |
| `DELETE` | `/admin/keys/{id}` | Revoke a key |
| `PATCH` | `/admin/keys/{id}` | Update scopes, rate limit, active status |
| `GET` | `/admin/keys/{id}/usage` | Usage stats for a key |
| `GET` | `/verify` | Token verification (called by Caddy forward_auth) |
| `GET` | `/services` | List available MCP servers |
| `GET` | `/health` | Gateway health |

**Admin API auth:** Separate `ADMIN_SECRET` environment variable. Admin requests require `X-Admin-Secret` header.

### 4.3 Cloudflare Tunnel (cloudflared)

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

### 4.4 MCP Server Containers (155+)

Each MCP server runs as an independent container:

- **Image:** `hackerdogs/{name}-mcp:latest` (pre-built on Docker Hub)
- **Transport:** `streamable-http` (set via `MCP_TRANSPORT` env var)
- **Port:** Unique per server (8100–8399 range)
- **Runtime:** Non-root user, tini init, Python 3.11/3.12
- **No exposed host ports** — only reachable within the Docker network via Caddy
- **Health check:** Each server exposes `/mcp/` which returns the MCP capability negotiation

---

## 5. Port Allocation Strategy

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

A canonical `port-map.json` file maps server names to ports, used by:
- The docker-compose generator script
- Caddy configuration
- Auth gateway service registry

---

## 6. Deployment & Configuration

### 6.1 Directory Structure

```
mcpfarm/
├── docker-compose.yml          # Generated — all 155+ services + infra
├── docker-compose.override.yml # Local overrides (API keys, dev settings)
├── .env                        # Environment variables (API keys, secrets)
├── .env.example                # Template
├── port-map.json               # Canonical server→port mapping
├── generate-compose.py         # Generates docker-compose.yml from port-map.json
│
├── caddy/
│   ├── Caddyfile               # Reverse proxy config
│   └── Dockerfile              # (optional) custom Caddy with plugins
│
├── auth-gateway/
│   ├── Dockerfile
│   ├── main.py                 # FastAPI auth service
│   ├── requirements.txt
│   └── seed_keys.py            # Bootstrap initial admin key
│
├── cloudflared/
│   ├── config.yml              # Tunnel config
│   └── credentials.json        # Tunnel credentials (gitignored)
│
└── scripts/
    ├── generate-compose.py     # Build the master compose file
    ├── health-check.sh         # Check all servers
    └── create-key.sh           # CLI to create API keys
```

### 6.2 Environment Variables (`.env`)

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

### 6.3 Launch Sequence

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

# 5. Seed the first admin API key
docker compose exec auth-gateway python seed_keys.py

# 6. Create user API keys
curl -X POST http://localhost:9090/admin/keys \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-agent", "scopes": "*"}'
# Returns: { "key": "hd_sk_a1b2c3d4...", "id": "..." }
```

### 6.4 Client Configuration

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

## 7. Architecture Decisions

### 7.1 Dynamic Routing in Caddy

**Problem:** 155+ servers each on a different internal port. Hard-coding 155 `reverse_proxy` blocks is fragile.

**Chosen approach: Caddy with dynamic upstreams via a route map file**

Caddy supports importing snippet files. A `generate-compose.py` script produces both the `docker-compose.yml` and a Caddy `routes.conf` from `port-map.json`:

```caddyfile
# routes.conf (auto-generated)
@julius-mcp path /julius-mcp/*
handle @julius-mcp {
    uri strip_prefix /julius-mcp
    reverse_proxy julius-mcp:8100
}

@naabu-mcp path /naabu-mcp/*
handle @naabu-mcp {
    uri strip_prefix /naabu-mcp
    reverse_proxy naabu-mcp:8105
}
# ... 153 more
```

**Alternative considered:** Caddy with a custom module or Lua-based routing. Rejected — adds build complexity and the auto-generated approach is deterministic and auditable.

### 7.2 Auth at Caddy vs. Auth at Each Server

**Chosen: Auth at Caddy (forward_auth)**

| Approach | Pros | Cons |
|----------|------|------|
| Caddy forward_auth | Single auth point, servers remain unmodified, easy to audit | Extra hop per request |
| Per-server middleware | No extra service | Must modify 155+ servers, inconsistent enforcement |
| Cloudflare Access | Zero-trust, no self-managed auth | Vendor lock-in, per-seat pricing, less flexible for API keys |

### 7.3 SQLite for Token Storage

**Why SQLite over Postgres/Redis:**

- **Self-contained:** No additional database service to manage
- **Performance:** WAL mode handles thousands of concurrent reads; token verification is a single indexed lookup (~0.01ms)
- **Durability:** Single file, easy to backup via volume mount
- **Scalability path:** If the farm grows beyond a single node, migrate to Turso (distributed SQLite) or Postgres with zero code changes to the auth gateway

**Scaling strategy:**

```
Phase 1 (current):  SQLite WAL on local volume
Phase 2 (multi-node): Turso/LiteFS for distributed SQLite
Phase 3 (enterprise):  Postgres + Redis cache for sub-ms lookups
```

### 7.4 Stateless & Isolated Design

| Property | How it's achieved |
|----------|-------------------|
| **Stateless MCP servers** | No volumes, no persistent data; tool results are computed and returned immediately |
| **Isolated** | Each server in its own container, own network namespace, non-root user, read-only filesystem possible |
| **Self-contained** | All 155+ servers + infra in one compose file; no external services required |
| **Reproducible** | Pre-built images pinned to `latest` (or SHA tags for production); `port-map.json` is the single source of truth |

---

## 8. Security Model

### 8.1 Network Isolation

```
Internet ──▶ Cloudflare ──▶ cloudflared ──▶ Caddy ──▶ MCP servers
                                               │
                                               ├── auth-gateway (internal only)
                                               └── MCP servers (internal only)
```

- **No host ports exposed** for MCP servers (only Caddy port 80 is on the Docker bridge, and even that is only accessed by cloudflared within the same network)
- **Internal Docker network** (`mcpfarm_internal`) isolates all containers
- **cloudflared** establishes outbound-only tunnel — no inbound firewall rules needed

### 8.2 Authentication Flow

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

### 8.3 Rate Limiting

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

### 8.4 Key Rotation

- Keys can be deactivated instantly via `PATCH /admin/keys/{id}` (set `is_active = false`)
- New keys created with `POST /admin/keys`
- Scoped keys restrict access to specific servers (e.g., `scopes: "naabu-mcp,trivy-mcp"`)
- Expired keys are automatically rejected (checked on every request)

---

## 9. Observability

### 9.1 Health Monitoring

**Caddy health endpoint:** `GET /health` returns 200 OK.

**Per-server health:** The auth-gateway periodically (every 30s) pings each MCP server's `/mcp/` endpoint and maintains a health registry. Exposed at `GET /services`:

```json
{
  "servers": [
    {
      "name": "naabu-mcp",
      "url": "/naabu-mcp/mcp/",
      "port": 8105,
      "status": "healthy",
      "last_check": "2026-03-14T12:00:00Z"
    },
    {
      "name": "trivy-mcp",
      "url": "/trivy-mcp/mcp/",
      "port": 8150,
      "status": "unhealthy",
      "last_check": "2026-03-14T12:00:00Z",
      "error": "connection refused"
    }
  ],
  "total": 155,
  "healthy": 153,
  "unhealthy": 2
}
```

### 9.2 Logging

- **Caddy:** Structured JSON access logs to stdout (Docker captures)
- **Auth gateway:** Request log table in SQLite for audit trail; structured logs to stdout
- **MCP servers:** stdout/stderr captured by Docker log driver
- **Aggregation:** Docker log driver can forward to any log sink (Loki, CloudWatch, etc.)

### 9.3 Metrics (Future)

- Prometheus metrics from auth-gateway (`/metrics`)
- Per-server request count, latency p50/p95/p99
- Per-key usage dashboards

---

## 10. Docker Compose Structure

The master `docker-compose.yml` follows this pattern:

```yaml
services:
  # ── Infrastructure ──
  caddy:
    image: caddy:2-alpine
    container_name: mcpfarm-caddy
    volumes:
      - ./caddy/Caddyfile:/etc/caddy/Caddyfile:ro
      - ./caddy/routes.conf:/etc/caddy/routes.conf:ro
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
    # No 'ports:' — only accessible via internal network

  naabu-mcp:
    image: hackerdogs/naabu-mcp:latest
    container_name: naabu-mcp
    environment:
      - MCP_TRANSPORT=streamable-http
      - MCP_PORT=8105
    networks:
      - mcpfarm
    restart: unless-stopped

  # ... 153 more servers ...

networks:
  mcpfarm:
    driver: bridge
    name: mcpfarm_internal

volumes:
  auth_data:
    name: mcpfarm_auth_data
```

**Key difference from current compose:** No `ports:` mapping on MCP servers. They are only reachable via the internal Docker network through Caddy.

---

## 11. Compose Generator Script

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
1. `docker-compose.yml` with all services
2. `caddy/routes.conf` with all route matchers
3. Validates no port collisions

---

## 12. Resource Requirements

### 12.1 Per-Server Footprint

| Resource | Idle | Active |
|----------|------|--------|
| Memory | 30–80 MB | 100–500 MB (tool-dependent) |
| CPU | ~0% | Burst during tool execution |
| Disk | 0 (stateless) | Temp files cleaned per-request |

### 12.2 Farm Totals (155 servers)

| Resource | Estimate |
|----------|----------|
| Memory (idle) | ~8–12 GB |
| Memory (10 concurrent) | ~12–16 GB |
| Disk (images) | ~40–60 GB |
| CPU | 4+ cores recommended |

### 12.3 Recommended Host

| Tier | Spec | Servers |
|------|------|---------|
| Dev/Test | 16 GB RAM, 4 CPU, 100 GB SSD | ~50 servers |
| Production | 32 GB RAM, 8 CPU, 200 GB SSD | All 155+ servers |
| High-load | 64 GB RAM, 16 CPU, 500 GB SSD | All servers + headroom |

---

## 13. Operational Runbook

### 13.1 Common Operations

```bash
# Start the entire farm
docker compose up -d

# Stop the entire farm
docker compose down

# Restart a single server
docker compose restart naabu-mcp

# View logs for a server
docker compose logs -f naabu-mcp

# Update all images
docker compose pull && docker compose up -d

# Check farm health
curl https://mcp.hackerdogs.ai/services

# Create an API key
curl -X POST http://localhost:9090/admin/keys \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -d '{"name": "my-agent", "scopes": "*"}'

# Revoke an API key
curl -X DELETE http://localhost:9090/admin/keys/{id} \
  -H "X-Admin-Secret: $ADMIN_SECRET"
```

### 13.2 Disaster Recovery

- **Auth DB backup:** `docker compose exec auth-gateway cp /data/auth.db /data/auth.db.bak`
- **Full farm restore:** `docker compose pull && docker compose up -d` (stateless servers need no restore)
- **Tunnel recovery:** cloudflared auto-reconnects; if persistent, recreate tunnel in Cloudflare dashboard

---

## 14. Future Enhancements

| Enhancement | Description | Priority |
|-------------|-------------|----------|
| **Server profiles** | Deploy subsets (e.g., "recon-only", "vuln-scan-only") via compose profiles | High |
| **Auto-scaling** | Spin up additional container replicas for hot servers | Medium |
| **Distributed SQLite** | Turso/LiteFS for multi-node auth | Medium |
| **Usage dashboard** | Grafana dashboard for per-key, per-server metrics | Medium |
| **MCP Gateway protocol** | Single MCP endpoint that multiplexes to all servers | Low |
| **Warm-start pool** | Keep N spare containers pre-warmed for cold-start-heavy servers | Low |
| **RBAC** | Role-based access control beyond simple scopes | Low |

---

## 15. Success Criteria

| Criteria | Target |
|----------|--------|
| Time from `docker compose up` to all servers healthy | < 120 seconds (pre-pulled images) |
| Time from `docker compose pull && up` to ready | < 10 minutes (first deploy) |
| Auth overhead per request | < 5ms |
| Concurrent MCP sessions supported | 100+ |
| Zero-downtime server updates | Rolling restart via `docker compose up -d --no-deps {server}` |
| Mean time to add new MCP server | < 5 minutes (add to port-map.json, regenerate) |

---

## 16. Open Questions

1. **Selective deployment:** Should we support deploying only a subset of servers via Docker Compose profiles (e.g., `--profile recon`, `--profile vuln`)?
2. **Cloudflare Access:** Should we add Cloudflare Access as a second auth layer in front of the tunnel, or is Bearer token auth sufficient?
3. **Per-server API keys:** Some MCP servers need upstream API keys (Shodan, ProjectDiscovery). Should these be passed at farm level (`.env`) or per-user via the auth gateway?
4. **WebSocket/SSE support:** Some future MCP transports may use WebSocket. Does Caddy + cloudflared handle long-lived connections correctly?
5. **Container resource limits:** Should we enforce per-container memory/CPU limits to prevent a runaway tool from starving the farm?
