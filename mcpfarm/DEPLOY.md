# Hackerdogs MCP Server Farm — Deployment Guide

## Prerequisites

- Docker Desktop (or Docker Engine on Linux) with at least 8 GB RAM allocated
- `docker compose` v2+
- `python3`
- A Cloudflare Tunnel token (from Zero Trust dashboard) — optional for local-only mode

---

## Quick Start

```bash
git clone <repo-url>
cd hd-mcpservers-docker/mcpfarm

# Public deployment (with Cloudflare tunnel)
TUNNEL_TOKEN=<your-token> ADMIN_SECRET=<your-secret> ./deploy.sh

# Local-only deployment (no tunnel, reachable at http://localhost:8485)
ADMIN_SECRET=<your-secret> ./deploy.sh --no-tunnel
```

That's it. The script handles everything end-to-end.

---

## Deploy Script

```bash
./deploy.sh [options]
```

| Option | Description |
|--------|-------------|
| *(none)* | Interactive — prompts for `TUNNEL_TOKEN`, generates `ADMIN_SECRET` |
| `--skip-build` | Skip image builds (images must already exist locally or in registry) |
| `--start-all` | Also start all 400 MCP server containers after infra is up |
| `--no-tunnel` | Local-only mode — skip cloudflared, farm at `http://localhost:8485` |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TUNNEL_TOKEN` | For public | Cloudflare tunnel token from Zero Trust dashboard |
| `ADMIN_SECRET` | No | Admin API password — auto-generated if not set |
| `FARM_PORT` | No | Host port for the farm (default: `8485`) |
| `MCPFARM_SECRETS_KEY` | No | Fernet key for encrypting stored LLM provider keys |
| `REDIS_URL` | No | Redis URL for vector index (default: `redis://hd-redis:6379`) |
| `MCPFARM_VECTOR_PREFIX` | No | Redis key prefix for vector docs (default: `mcpfarm:v1`) |
| `MCPFARM_VECTOR_INDEX` | No | RediSearch index name (default: `mcpfarm:idx`) |
| `VECTOR_DIM` | No | Embedding dimension (default: `1536`) |
| `EMBED_PROVIDER` | No | Embeddings backend: `openai`, `ollama`, `local`, `auto` (default: `auto`) |
| `OPENAI_API_KEY` | No | For OpenAI embeddings and server-side chat proxy |
| `OLLAMA_URL` | No | Ollama base URL (default: `http://host.docker.internal:11434`) |

The script writes `TUNNEL_TOKEN`, `ADMIN_SECRET`, and `FARM_PORT` to `.env` in the `mcpfarm/` directory.

---

## What the Script Does

1. **Checks prerequisites** — Docker running, python3 available
2. **Writes `.env`** — `TUNNEL_TOKEN` + `ADMIN_SECRET` + `FARM_PORT`
3. **Builds images** — all MCP server images from their Dockerfiles (skipped with `--skip-build`)
4. **Starts auth-gateway** — waits until healthy before proceeding
5. **Starts Caddy** — reverse proxy on port `FARM_PORT` (default 8485) and admin API on 2019
6. **Starts cloudflared** — Cloudflare tunnel (shares Caddy's network namespace) — skipped with `--no-tunnel`
7. **Seeds the database** — registers all 400 servers, creates admin API key
8. **Loads Caddy routes** — generates and hot-reloads all 400 proxy routes
9. **Verifies** — health check + tunnel connection count + farm stats

---

## First Deploy vs Re-Deploy

### First deploy (fresh machine)

Building ~400 images from source takes **30–60 minutes**. Run without `--skip-build`:

```bash
TUNNEL_TOKEN=xxx ./deploy.sh
```

Save the **Admin API Key** printed at the end — it is only shown once.

### Re-deploy (same machine, updated code)

```bash
TUNNEL_TOKEN=xxx ADMIN_SECRET=xxx ./deploy.sh --skip-build
```

### Re-deploy to a new machine (using DockerHub)

All 400 server images and the two farm infra images are published to DockerHub under the `hackerdogs/` namespace. On a fresh machine:

```bash
TUNNEL_TOKEN=xxx ./deploy.sh --skip-build
```

Docker will pull images from DockerHub instead of building them.

### Publishing farm infra images

Both infra components have their own publish scripts:

```bash
# Auth gateway
cd mcpfarm/auth-gateway
./publish_to_hackerdogs.sh hackerdogs

# Farm UI
cd mcpfarm-ui
./publish_to_hackerdogs.sh hackerdogs
```

These build multi-arch (linux/amd64 + linux/arm64) images and push to DockerHub with retry logic.

---

## Architecture

```
Internet
   │
   ▼
Cloudflare Edge  (mcpservers-dev.hackerdogs.ai)
   │  QUIC tunnel
   ▼
cloudflared  ──── localhost:8485 ────▶  Caddy :80
                                              │
                          ┌───────────────────┤
                          │  /verify          │  /{server}/mcp
                          ▼                   ▼
                    auth-gateway        MCP Server
                    (FastAPI :9090)      (uvicorn)
                    SQLite DB
                    Redis (vectors)
```

### Components

| Component | Container | Image | Description |
|-----------|-----------|-------|-------------|
| **Caddy** | `mcpfarm-caddy` | `caddy:2-alpine` | Reverse proxy with `forward_auth` for token verification |
| **Auth Gateway** | `mcpfarm-auth` | `hackerdogs/auth-gateway` | API, auth, health monitoring, chat proxy, vector index |
| **Farm UI** | `mcpfarm-ui` | `hackerdogs/mcpfarm-ui` | Web dashboard for managing the farm |
| **Cloudflared** | `mcpfarm-tunnel` | `cloudflare/cloudflared` | Outbound-only tunnel to Cloudflare edge |
| **MCP Servers** | `{name}-mcp` | `hackerdogs/{name}-mcp` | 400 containerised tools on `mcpfarm` network |

---

## Configuration

### Server-level environment variables

Each MCP server accepts tool-specific API keys via environment variables defined in `docker-compose.yml` and `.env`. Common variables across servers:

| Variable | Description |
|----------|-------------|
| `MCP_TRANSPORT` | Transport protocol: `stdio` or `streamable-http` |
| `MCP_PORT` | HTTP port for the server (assigned from `port-map.json`) |

### Chat and vector search configuration

The auth-gateway includes a server-side LLM proxy and vector search for dynamic tool binding:

| Variable | Description |
|----------|-------------|
| `MCPFARM_SECRETS_KEY` | Fernet key for encrypting stored LLM API keys at rest |
| `EMBED_PROVIDER` | Embeddings backend: `openai` (requires key), `ollama`, `local` (CPU, 256-dim), `auto` |
| `VECTOR_AUTO_REINDEX` | Auto-reindex on startup (`true`/`false`, default `false`) |
| `REDIS_URL` | Redis connection for vector index (default: `redis://hd-redis:6379`) |

### LLM key vault

LLM provider API keys are stored encrypted in the auth-gateway and decrypted server-side for chat completions. Manage via the API:

```bash
# Store a key
curl -X PUT "$BASE/llm-keys/openai" \
  -H "X-Admin-Secret: $SECRET" \
  -H "Content-Type: application/json" \
  -d '{"key": "sk-..."}'

# List stored providers (keys are masked)
curl "$BASE/llm-keys" -H "X-Admin-Secret: $SECRET"

# Delete a key
curl -X DELETE "$BASE/llm-keys/openai" -H "X-Admin-Secret: $SECRET"
```

Supported providers: `openai`, `claude`, `ollama`, `bedrock`, `azure_openai`, `openrouter`, `grok`, `gemini`.

---

## Admin API Reference

All admin endpoints require the `X-Admin-Secret` header (plus a valid `Authorization: Bearer <API_KEY>` for endpoints that also pass through the auth middleware).

### Public endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (returns `{"status": "ok"}`) |
| `GET` | `/services` | List all registered servers and their status |
| `GET` | `/services/{name}/readme` | Fetch README markdown for a server |
| `GET` | `/ui-config` | UI bootstrap config (base URL, auto-generated key) |

### Server management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/admin/servers` | List all servers with full details |
| `GET` | `/admin/servers/{name}` | Get a single server |
| `POST` | `/admin/servers` | Create a new server (Docker image or external URL) |
| `DELETE` | `/admin/servers/{name}` | Delete a server (stops container, removes DB entry) |
| `POST` | `/admin/servers/import` | Import from Claude Desktop / Cursor JSON config |
| `PATCH` | `/admin/servers/{name}/env` | Update environment variables for a server |
| `POST` | `/admin/servers/{name}/start` | Start a server container |
| `POST` | `/admin/servers/{name}/stop` | Stop a server container |
| `POST` | `/admin/servers/{name}/restart` | Restart a server container |
| `POST` | `/admin/servers/{name}/enable` | Enable routing (add to Caddy) |
| `POST` | `/admin/servers/{name}/disable` | Disable routing (remove from Caddy) |
| `GET` | `/admin/servers/{name}/health` | Health-check a single server |
| `GET` | `/admin/servers/{name}/tools` | List MCP tools exposed by a running server |
| `GET` | `/admin/servers/{name}/logs` | Fetch container logs |

### Automation API

These endpoints are designed for scripting and batch operations:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/admin/servers/batch` | Run start/stop/restart/enable/disable on multiple servers |
| `POST` | `/admin/servers/health-check` | Health-check all servers (or a named subset) |
| `GET` | `/admin/servers/search` | Search/filter servers by name, category, status, source, health |
| `GET` | `/admin/servers/categories` | List all server categories with counts |

#### Batch operations

```bash
# Stop multiple servers at once
curl -X POST "$BASE/admin/servers/batch" \
  -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"servers": ["nmap-mcp", "trivy-mcp", "nuclei-mcp"], "action": "stop"}'

# Valid actions: start, stop, restart, enable, disable
```

#### Batch health check

```bash
# Check all servers
curl -X POST "$BASE/admin/servers/health-check" \
  -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY"

# Check specific servers
curl -X POST "$BASE/admin/servers/health-check" \
  -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '["nmap-mcp", "sqlmap-mcp"]'

# Response: {"total": 2, "healthy": 1, "unhealthy": 1, "results": [...]}
```

#### Search and filter

```bash
# Search by name substring
curl "$BASE/admin/servers/search?q=nmap" -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY"

# Filter by category
curl "$BASE/admin/servers/search?category=recon" -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY"

# Filter by status
curl "$BASE/admin/servers/search?status=running" -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY"

# Filter by health
curl "$BASE/admin/servers/search?healthy=true" -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY"

# Combine filters
curl "$BASE/admin/servers/search?category=recon&status=running&healthy=true" \
  -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY"

# Response: {"count": 5, "servers": [...]}
```

#### List categories

```bash
curl "$BASE/admin/servers/categories" -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY"
# Response: {"categories": [{"category": "misc", "count": 86}, {"category": "network-recon", "count": 52}, ...]}
```

### API key management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/admin/keys` | List all API keys (hashed, never plaintext) |
| `POST` | `/admin/keys` | Create a new API key (plaintext returned once) |
| `GET` | `/admin/keys/{id}` | Get key metadata |
| `PATCH` | `/admin/keys/{id}` | Update key (scopes, rate limit, active status) |
| `DELETE` | `/admin/keys/{id}` | Revoke an API key |
| `GET` | `/admin/keys/{id}/usage` | Per-server usage breakdown for a key |

### Chat and vector search

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat/completions` | Server-side LLM completion (keys decrypted server-side) |
| `POST` | `/vectors/search` | Vector search for dynamic tool binding |
| `GET` | `/llm-keys` | List configured LLM providers (masked) |
| `PUT` | `/llm-keys/{provider}` | Store an encrypted LLM provider key |
| `DELETE` | `/llm-keys/{provider}` | Delete a stored LLM provider key |
| `POST` | `/admin/vectors/reindex` | Trigger full vector reindex |
| `GET` | `/admin/vectors/stats` | Vector index statistics |
| `POST` | `/admin/vectors/index-server/{name}` | Index a single server's tools |

### Farm operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/admin/stats` | Farm summary (servers, keys, requests) |
| `GET` | `/admin/audit` | Request audit log (filterable by key, server, date) |
| `GET` | `/admin/export` | Export full config as JSON |
| `POST` | `/admin/reload` | Regenerate and hot-reload all Caddy routes |
| `POST` | `/admin/rotate-secret` | Rotate the admin secret (returns new secret + key) |

---

## Manual Operations

### Start / stop individual MCP servers

```bash
# Via API (preferred)
curl -X POST "$BASE/admin/servers/nmap-mcp/start" \
  -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY"

# Via docker compose
docker compose up -d --no-deps nmap-mcp
docker compose stop nmap-mcp
```

### Batch operations via API

```bash
# Start a group of recon servers
curl -X POST "$BASE/admin/servers/batch" \
  -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"servers": ["nmap-mcp", "shodan-mcp", "nuclei-mcp", "whois-mcp"], "action": "start"}'
```

### Add a new server dynamically

```bash
# Add an external MCP server (HTTP endpoint)
curl -X POST "$BASE/admin/servers" \
  -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-custom-mcp", "url": "https://my-server.example.com/mcp", "category": "custom"}'

# Add a Docker-based server
curl -X POST "$BASE/admin/servers" \
  -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-tool-mcp", "image": "myregistry/my-tool-mcp:latest", "category": "custom"}'

# Import from Claude Desktop config
curl -X POST "$BASE/admin/servers/import" \
  -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"mcpServers": {"my-tool": {"url": "https://my-tool.example.com/mcp"}}}'
```

### Check what's running

```bash
curl "$BASE/admin/stats" -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY"
```

### Reload Caddy routes (after adding/removing servers)

```bash
curl -X POST "$BASE/admin/reload" -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY"
```

### View logs

```bash
docker logs mcpfarm-auth       # auth gateway
docker logs mcpfarm-caddy      # caddy
docker logs mcpfarm-tunnel     # cloudflare tunnel
docker logs nmap-mcp           # any MCP server
```

---

## Testing

### Automated test suite

The auth-gateway includes a comprehensive test suite (42 tests) covering health, auth, CRUD, search, batch operations, API keys, LLM keys, stats, audit, export, import, and chat.

```bash
cd mcpfarm/auth-gateway

# Create test venv (first time only)
python3 -m venv .venv-test
.venv-test/bin/pip install -r requirements.txt pytest

# Run tests
.venv-test/bin/python -m pytest tests/test_farm_api.py -v
```

Tests use an isolated SQLite database and mock Redis namespace — they do not touch the live farm.

### Live farm smoke test

```bash
BASE="http://localhost:8485"
KEY="<your-api-key>"
SECRET="<your-admin-secret>"

# Health
curl -s "$BASE/health"

# List servers
curl -s "$BASE/services" -H "Authorization: Bearer $KEY" | python3 -m json.tool | head -20

# Search
curl -s "$BASE/admin/servers/search?q=nmap" \
  -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY"

# Categories
curl -s "$BASE/admin/servers/categories" \
  -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY"

# Stats
curl -s "$BASE/admin/stats" \
  -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY"
```

---

## Connecting an MCP Client

### URL pattern

```
https://mcpservers-dev.hackerdogs.ai/{server-name}/mcp
```

For local deployments:
```
http://localhost:8485/{server-name}/mcp
```

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "nmap": {
      "type": "http",
      "url": "https://mcpservers-dev.hackerdogs.ai/nmap-mcp/mcp",
      "headers": {
        "Authorization": "Bearer <API_KEY>"
      }
    },
    "whois": {
      "type": "http",
      "url": "https://mcpservers-dev.hackerdogs.ai/whois-mcp/mcp",
      "headers": {
        "Authorization": "Bearer <API_KEY>"
      }
    }
  }
}
```

### MCP Inspector (browser UI)

```bash
npx @modelcontextprotocol/inspector
```

Set transport to **Streamable HTTP**, URL to the server endpoint, and add the `Authorization` header.

### curl (manual test)

```bash
KEY="<API_KEY>"
BASE="https://mcpservers-dev.hackerdogs.ai/whois-mcp/mcp"

# 1. Initialize — get session ID
curl -s -D - "$BASE" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  | grep -i mcp-session-id

# 2. Send initialized notification
curl -s "$BASE" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: <SESSION_ID>" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'

# 3. List tools
curl -s "$BASE" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: <SESSION_ID>" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'

# 4. Call a tool
curl -s "$BASE" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: <SESSION_ID>" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"whois_lookup","arguments":{"domain":"example.com"}}}'
```

---

## Publishing Docker Images

### Individual MCP server images

Each server directory has a `publish_to_hackerdogs.sh` script:

```bash
cd nmap-mcp
./publish_to_hackerdogs.sh hackerdogs                    # Build + publish
./publish_to_hackerdogs.sh --build hackerdogs            # Build only
./publish_to_hackerdogs.sh --publish hackerdogs           # Publish only (image must exist)
./publish_to_hackerdogs.sh --platforms sequential hackerdogs  # Build amd64 then arm64 separately
```

### Farm infra images

```bash
# Auth gateway
cd mcpfarm/auth-gateway
./publish_to_hackerdogs.sh hackerdogs

# Farm UI
cd mcpfarm-ui
./publish_to_hackerdogs.sh hackerdogs
```

All images are multi-arch (linux/amd64 + linux/arm64) with automatic retry logic for transient Docker Hub failures.

---

## Known Build Failures

| Server | Reason | Status |
|--------|--------|--------|
| `aws-core-mcp` | AWS removed `awslabs.core-mcp-server` from PyPI | Blocked upstream — cannot build |

All other 399 server images build and run. If a future change breaks a build, add that server to `FAIL_BUILDS` in `deploy.sh` to skip it on `--start-all`.

---

## Resource Guidelines

| Containers running | Recommended RAM | Recommended CPUs |
|-------------------|-----------------|------------------|
| Infra only (3–4) | 2 GB | 2 |
| Infra + 50 servers | 4 GB | 4 |
| Infra + 200 servers | 8 GB | 6 |
| Full farm (400) | 16 GB+ | 8+ |

Servers are set to `restart: 'no'` — they only run when explicitly started. Start only what you need to avoid overloading Docker Desktop.
