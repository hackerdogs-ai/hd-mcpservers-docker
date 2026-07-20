# Hackerdogs MCP Server Farm — Deployment Guide

The farm is **only** Docker Compose services: Caddy, auth-gateway, the UI, and MCP server containers. It listens on `FARM_PORT` (default **8485**). TLS, Cloudflare Tunnel, nginx, ALBs, and any other edge proxy are **outside** the farm — put them in front of `:8485` yourself if you need them. `deploy.sh` never configures or depends on a tunnel.

## Prerequisites

- Docker Desktop (or Docker Engine on Linux) with at least 8 GB RAM allocated
- `docker compose` v2+
- `python3`

---

## Quick Start

You need the `mcpfarm/` directory from this repo (compose, Caddyfile, `port-map.json`). Images come from Docker Hub — no local build required when using `--skip-build` or plain `docker compose pull`.

### With `deploy.sh`

Wraps secret/`.env` setup, ordered startup + health waits, DB seed, and Caddy route reload in one command.

```bash
git clone <repo-url>
cd hd-mcpservers-docker/mcpfarm

# Start infra (auth-gateway + Caddy + UI), seed DB, load routes
ADMIN_SECRET=<your-secret> ./deploy.sh up --skip-build

# Start the tools you need
./deploy.sh start naabu-mcp nuclei-mcp

# Check status
./deploy.sh status
```

### Docker Compose only (no scripts)

Same outcome as `./deploy.sh up --skip-build` + `start`, using only Compose / `curl` / `docker exec`:

```bash
git clone <repo-url>
cd hd-mcpservers-docker/mcpfarm

docker network create hdnet 2>/dev/null || true
echo "ADMIN_SECRET=<your-secret>" > .env

docker compose pull auth-gateway caddy mcpfarm-ui
docker compose up -d --no-deps auth-gateway
docker compose up -d --no-deps caddy
docker compose up -d --no-deps mcpfarm-ui

docker exec mcpfarm-auth python seed.py
curl -s -X POST http://localhost:8485/admin/reload \
  -H "X-Admin-Secret: <your-secret>"

docker compose up -d --pull never --no-deps naabu-mcp nuclei-mcp
```

Host port defaults to **8485**. To change it, set `FARM_PORT` in `.env` (see [`.env.example`](./.env.example)).

A pure “images only / no clone” path is **not** supported today: Caddy and the auth-gateway mount files from this directory (`caddy/Caddyfile`, `port-map.json`, and the repo for README indexing).

Farm UI: `http://localhost:8485`  
Health: `http://localhost:8485/health`

Save the **Admin API Key** printed by `up` / `seed` — it is only shown once.

---

## deploy.sh commands

```bash
./deploy.sh help
./deploy.sh up [--skip-build] [--start-all]
./deploy.sh down
./deploy.sh start <name>-mcp ... | --all
./deploy.sh stop  <name>-mcp ... | --all | --infra
./deploy.sh restart <name>-mcp ... | --all | --infra
./deploy.sh status
./deploy.sh reload
./deploy.sh seed
```

| Command | Description |
|---------|-------------|
| `up` | Build (unless `--skip-build`), start infra, seed DB, reload Caddy routes |
| `up --start-all` | Same as `up`, then start every MCP server (16+ GB RAM recommended) |
| `down` | `docker compose down` — stop and remove infra + MCP containers |
| `start` / `stop` / `restart` | Lifecycle for named MCP servers, or `--all` / `--infra` |
| `status` | Infra containers, health endpoint, running MCP containers, admin stats |
| `reload` | Hot-reload all Caddy routes via the auth-gateway |
| `seed` | Re-register servers from `port-map.json` |

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ADMIN_SECRET` | Recommended | Admin API password — auto-generated on first `up` if unset |
| `FARM_PORT` | No | Host port for Caddy (default: `8485`) |
| `FARM_HTTP` | No | URL used by the script for health/admin calls (default: `http://localhost:$FARM_PORT`) |
| `MCPFARM_SECRETS_KEY` | Production | Fernet key for encrypting stored LLM provider keys |
| `REDIS_URL` | No | Redis URL for vector index (default: `redis://hd-redis:6379`) |
| `MCPFARM_VECTOR_PREFIX` | No | Redis key prefix (default: `mcpfarm:v1`) |
| `MCPFARM_VECTOR_INDEX` | No | RediSearch index name (default: `mcpfarm:idx`) |
| `VECTOR_DIM` | No | Embedding dimension (default: `1536`) |
| `EMBED_PROVIDER` | No | `openai`, `ollama`, `local`, or `auto` (default: `auto`) |
| `OPENAI_API_KEY` | No | For OpenAI embeddings and server-side chat proxy |
| `OLLAMA_URL` | No | Ollama base URL (default: `http://host.docker.internal:11434`) |

`up` writes `ADMIN_SECRET` and `FARM_PORT` into `.env` in this directory. See [`.env.example`](./.env.example) for the full list including tool API keys.

---

## What `up` does

1. Checks Docker and python3
2. Ensures `ADMIN_SECRET` / `.env`
3. Builds auth-gateway, UI, and MCP images (skipped with `--skip-build`)
4. Starts **auth-gateway** → **caddy** → **mcpfarm-ui**
5. Seeds the database (registers servers from `port-map.json`)
6. Reloads Caddy routes
7. Optionally starts all MCP servers (`--start-all`)
8. Prints health + admin stats

MCP server containers use `restart: 'no'` — they only run when you `start` them (UI, API, or `./deploy.sh start`).

---

## Local vs production

Both use the same command. The farm always binds host port `FARM_PORT`.

### Local

```bash
ADMIN_SECRET=devsecret ./deploy.sh up --skip-build
./deploy.sh start naabu-mcp
```

Reach the farm at `http://localhost:8485`.

### Production

```bash
ADMIN_SECRET=<strong-secret> \
MCPFARM_SECRETS_KEY=<fernet-key> \
./deploy.sh up --skip-build
```

Then terminate TLS / publish the farm **in front of** port 8485 with whatever you already use (Cloudflare Tunnel, Caddy, nginx, ALB, Tailscale, etc.). Forward `Authorization` and `mcp-session-id` unchanged.

Example (edge is your problem, not the farm's):

```
Internet → your TLS proxy / tunnel → http://farm-host:8485 → Caddy → MCP servers
```

**Checklist:**

- [ ] Strong `ADMIN_SECRET` in a secrets manager
- [ ] `MCPFARM_SECRETS_KEY` set for the LLM vault
- [ ] External Redis if not using the shared `hd-redis` network
- [ ] Prefer `./deploy.sh up --skip-build` on fresh hosts (pull from Docker Hub)
- [ ] Start only needed servers (`./deploy.sh start …`), not `--start-all`, unless you have 16+ GB RAM
- [ ] Create scoped API keys via `POST /admin/keys`
- [ ] `POST /admin/vectors/reindex` after first deploy for chat tool binding

### Publishing farm infra images

```bash
cd mcpfarm/auth-gateway && ./publish_to_hackerdogs.sh hackerdogs
cd mcpfarm-ui && ./publish_to_hackerdogs.sh hackerdogs
```

Multi-arch (amd64 + arm64) with retry logic.

---

## Architecture

```
Client (or your TLS edge)
   │
   ▼
Caddy :8485  ──forward_auth──▶  auth-gateway :9090
   │                                 │
   │                                 ├── SQLite (keys, audit)
   │                                 └── Redis (vectors)
   ▼
MCP server containers (on demand)
```

| Component | Container | Image | Description |
|-----------|-----------|-------|-------------|
| **Caddy** | `mcpfarm-caddy` | `caddy:2-alpine` | Reverse proxy + `forward_auth` |
| **Auth Gateway** | `mcpfarm-auth` | `hackerdogs/auth-gateway` | Auth, admin API, chat proxy, vector index |
| **Farm UI** | `mcpfarm-ui` | `hackerdogs/mcpfarm-ui` | Web dashboard |
| **MCP Servers** | `{name}-mcp` | `hackerdogs/{name}-mcp` | Tools from `port-map.json` |

Compose file: [`docker-compose.yml`](./docker-compose.yml) (generated/maintained from [`port-map.json`](./port-map.json)). There is **no** root-level repo `docker-compose.yml` — use this farm compose, or each tool's own `docker-compose.yml` for standalone runs.

---

## Configuration

### Server-level environment variables

| Variable | Description |
|----------|-------------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` |
| `MCP_PORT` | HTTP port from `port-map.json` |

Tool-specific keys are listed in `port-map.json` (`env` arrays) and `.env.example`.

### Chat and vector search

| Variable | Description |
|----------|-------------|
| `MCPFARM_SECRETS_KEY` | Fernet key for LLM API keys at rest |
| `EMBED_PROVIDER` | `openai`, `ollama`, `local`, or `auto` |
| `VECTOR_AUTO_REINDEX` | Auto-reindex on startup (`true`/`false`) |
| `REDIS_URL` | Redis for vector index |

### LLM key vault

```bash
BASE="http://localhost:8485"
SECRET="<ADMIN_SECRET>"

curl -X PUT "$BASE/llm-keys/openai" \
  -H "X-Admin-Secret: $SECRET" \
  -H "Content-Type: application/json" \
  -d '{"key": "sk-..."}'

curl "$BASE/llm-keys" -H "X-Admin-Secret: $SECRET"
curl -X DELETE "$BASE/llm-keys/openai" -H "X-Admin-Secret: $SECRET"
```

Supported providers: `openai`, `claude`, `ollama`, `bedrock`, `azure_openai`, `openrouter`, `grok`, `gemini`.

---

## Admin API Reference

All admin endpoints require the `X-Admin-Secret` header (plus a valid `Authorization: Bearer <API_KEY>` for endpoints that also pass through the auth middleware).

### Public endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/services` | List registered servers |
| `GET` | `/services/{name}/readme` | README markdown |
| `GET` | `/ui-config` | UI bootstrap config |

### Server management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/admin/servers` | List servers |
| `GET` | `/admin/servers/{name}` | Get one server |
| `POST` | `/admin/servers` | Create server (image or URL) |
| `DELETE` | `/admin/servers/{name}` | Delete server |
| `POST` | `/admin/servers/import` | Import Claude/Cursor JSON |
| `PATCH` | `/admin/servers/{name}/env` | Update env vars |
| `POST` | `/admin/servers/{name}/start` | Start container |
| `POST` | `/admin/servers/{name}/stop` | Stop container |
| `POST` | `/admin/servers/{name}/restart` | Restart container |
| `POST` | `/admin/servers/{name}/enable` | Enable Caddy route |
| `POST` | `/admin/servers/{name}/disable` | Disable Caddy route |
| `GET` | `/admin/servers/{name}/health` | Health-check one |
| `GET` | `/admin/servers/{name}/tools` | List MCP tools |
| `GET` | `/admin/servers/{name}/logs` | Container logs |

### Automation API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/admin/servers/batch` | Batch start/stop/restart/enable/disable |
| `POST` | `/admin/servers/health-check` | Health-check all or a subset |
| `GET` | `/admin/servers/search` | Search/filter |
| `GET` | `/admin/servers/categories` | Categories with counts |

```bash
# Batch stop
curl -X POST "$BASE/admin/servers/batch" \
  -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"servers": ["nmap-mcp", "trivy-mcp"], "action": "stop"}'

# Search
curl "$BASE/admin/servers/search?q=nmap&status=running" \
  -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY"
```

### API key management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/admin/keys` | List keys (hashed) |
| `POST` | `/admin/keys` | Create key (plaintext once) |
| `GET` | `/admin/keys/{id}` | Key metadata |
| `PATCH` | `/admin/keys/{id}` | Update scopes / rate limit / active |
| `DELETE` | `/admin/keys/{id}` | Revoke |
| `GET` | `/admin/keys/{id}/usage` | Per-server usage |

### Chat and vectors

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat/completions` | Server-side LLM completion |
| `POST` | `/vectors/search` | Vector tool search |
| `GET`/`PUT`/`DELETE` | `/llm-keys[/{provider}]` | LLM vault |
| `POST` | `/admin/vectors/reindex` | Full reindex |
| `GET` | `/admin/vectors/stats` | Index stats |
| `POST` | `/admin/vectors/index-server/{name}` | Index one server |

### Farm operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/admin/stats` | Farm summary |
| `GET` | `/admin/audit` | Audit log |
| `GET` | `/admin/export` | Export config JSON |
| `POST` | `/admin/reload` | Reload Caddy routes |
| `POST` | `/admin/rotate-secret` | Rotate admin secret |

---

## Manual operations

Prefer `./deploy.sh start|stop|status`, or:

```bash
# Via API
curl -X POST "$BASE/admin/servers/nmap-mcp/start" \
  -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY"

# Via compose
docker compose up -d --no-deps nmap-mcp
docker compose stop nmap-mcp
```

```bash
docker logs mcpfarm-auth
docker logs mcpfarm-caddy
docker logs nmap-mcp
```

---

## Testing

```bash
cd mcpfarm/auth-gateway
python3 -m venv .venv-test
.venv-test/bin/pip install -r requirements.txt pytest
.venv-test/bin/python -m pytest tests/test_farm_api.py -v
```

Live smoke:

```bash
BASE="http://localhost:8485"
KEY="<api-key>"
SECRET="<admin-secret>"

curl -s "$BASE/health"
curl -s "$BASE/services" -H "Authorization: Bearer $KEY" | python3 -m json.tool | head
curl -s "$BASE/admin/stats" -H "X-Admin-Secret: $SECRET" -H "Authorization: Bearer $KEY"
```

---

## Connecting an MCP client

```
http://localhost:8485/{server-name}/mcp
```

Behind your own TLS edge:

```
https://mcpservers.example.com/{server-name}/mcp
```

```json
{
  "mcpServers": {
    "nmap": {
      "type": "http",
      "url": "http://localhost:8485/nmap-mcp/mcp",
      "headers": {
        "Authorization": "Bearer <API_KEY>"
      }
    }
  }
}
```

MCP Inspector: `npx @modelcontextprotocol/inspector` — Streamable HTTP + `Authorization` header.

---

## Publishing Docker images

```bash
# Individual MCP server
cd nmap-mcp
./publish_to_hackerdogs.sh hackerdogs

# Farm infra
cd mcpfarm/auth-gateway && ./publish_to_hackerdogs.sh hackerdogs
cd mcpfarm-ui && ./publish_to_hackerdogs.sh hackerdogs
```

---

## Known build failures

| Server | Reason | Status |
|--------|--------|--------|
| `aws-core-mcp` | AWS removed `awslabs.core-mcp-server` from PyPI | Blocked upstream |

Skip broken builds when using `start --all` if needed.

---

## Resource guidelines

| Containers running | Recommended RAM | Recommended CPUs |
|-------------------|-----------------|------------------|
| Infra only (3) | 2 GB | 2 |
| Infra + 50 servers | 4 GB | 4 |
| Infra + 200 servers | 8 GB | 6 |
| Full farm (~400) | 16 GB+ | 8+ |

End-user UI guide: [mcpfarm-ui/docs/USERS-GUIDE.md](../mcpfarm-ui/docs/USERS-GUIDE.md).
