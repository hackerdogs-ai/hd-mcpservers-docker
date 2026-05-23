# Hackerdogs MCP Server Farm — Deployment Guide

## Prerequisites

- Docker Desktop (or Docker Engine on Linux) with at least 8GB RAM allocated
- `docker compose` v2+
- `python3`
- A Cloudflare Tunnel token (from Zero Trust dashboard)

---

## Quick Start

```bash
git clone <repo-url>
cd hd-mcpservers-docker/mcpfarm

TUNNEL_TOKEN=<your-token> ADMIN_SECRET=<your-secret> ./deploy.sh
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
| `--start-all` | Also start all 386 MCP server containers after infra is up |

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TUNNEL_TOKEN` | Yes | Cloudflare tunnel token from Zero Trust dashboard |
| `ADMIN_SECRET` | No | Admin API password — auto-generated if not set |

The script writes these to `.env` in the `mcpfarm/` directory.

---

## What the Script Does

1. **Checks prerequisites** — Docker running, python3 available
2. **Writes `.env`** — `TUNNEL_TOKEN` + `ADMIN_SECRET`
3. **Builds images** — all MCP server images from their Dockerfiles (skipped with `--skip-build`)
4. **Starts auth-gateway** — waits until healthy before proceeding
5. **Starts Caddy** — reverse proxy on ports 80 and 11459
6. **Starts cloudflared** — Cloudflare tunnel (shares Caddy's network namespace)
7. **Seeds the database** — registers all 386 servers, creates admin API key
8. **Loads Caddy routes** — generates and hot-reloads all 386 proxy routes
9. **Verifies** — health check + tunnel connection count + farm stats

---

## First Deploy vs Re-Deploy

### First deploy (fresh machine)

Building ~380 images from source takes **30–60 minutes**. Run without `--skip-build`:

```bash
TUNNEL_TOKEN=xxx ./deploy.sh
```

Save the **Admin API Key** printed at the end — it is only shown once.

### Re-deploy (same machine, updated code)

```bash
TUNNEL_TOKEN=xxx ADMIN_SECRET=xxx ./deploy.sh --skip-build
```

### Re-deploy to a new machine (using a registry)

Push images from the source machine first:

```bash
docker images --format "{{.Repository}}:{{.Tag}}" | grep hackerdogs | \
  xargs -I{} docker push {}
```

Then on the target machine:

```bash
TUNNEL_TOKEN=xxx ./deploy.sh --skip-build
```

Docker will pull the images from the registry instead of building them.

---

## Manual Operations

### Start / stop individual MCP servers

```bash
# Start one server
docker compose up -d --no-deps nmap-mcp

# Stop one server
docker compose stop nmap-mcp

# Start a group
docker compose up -d --no-deps nmap-mcp shodan-mcp nuclei-mcp whois-mcp
```

### Check what's running

```bash
docker info --format "{{.ContainersRunning}}/{{.Containers}} running"

curl http://localhost/admin/stats \
  -H "X-Admin-Secret: <ADMIN_SECRET>"
```

### Reload Caddy routes (after adding/removing servers)

```bash
curl -X POST http://localhost/admin/reload \
  -H "X-Admin-Secret: <ADMIN_SECRET>"
```

### View logs

```bash
docker logs mcpfarm-auth       # auth gateway
docker logs mcpfarm-caddy      # caddy
docker logs mcpfarm-tunnel     # cloudflare tunnel
docker logs nmap-mcp           # any MCP server
```

---

## Architecture

```
Internet
   │
   ▼
Cloudflare Edge  (mcpservers-dev.hackerdogs.ai)
   │  QUIC tunnel
   ▼
cloudflared  ──── localhost:11459 ────▶  Caddy :80/:11459
                                              │
                          ┌───────────────────┤
                          │  /verify          │  /{server}/mcp
                          ▼                   ▼
                    auth-gateway        MCP Server
                    (FastAPI)           (uvicorn)
                    SQLite DB
```

- **Cloudflare tunnel** — zero open inbound ports; outbound only
- **Caddy** — reverse proxy with `forward_auth` for token verification on every request
- **Auth gateway** — bearer token validation, admin API, health monitoring
- **MCP servers** — 386 containerised security tools on the internal `mcpfarm` network

---

## Connecting an MCP Client

### URL pattern

```
https://mcpservers-dev.hackerdogs.ai/{server-name}/mcp
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

## Admin API

All admin endpoints require `X-Admin-Secret: <ADMIN_SECRET>` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Public health check |
| `GET` | `/services` | List all registered servers and their status |
| `GET` | `/admin/stats` | Farm summary (keys, servers, requests) |
| `GET` | `/admin/keys` | List API keys |
| `POST` | `/admin/keys` | Create a new API key |
| `DELETE` | `/admin/keys/{key_id}` | Revoke an API key |
| `GET` | `/admin/servers` | List servers with health status |
| `POST` | `/admin/reload` | Regenerate and hot-reload all Caddy routes |
| `GET` | `/admin/audit` | Request audit log |
| `GET` | `/admin/export` | Export full config as JSON |

---

## Known Build Failures

Six servers cannot be built due to upstream issues:

| Server | Reason |
|--------|--------|
| `bettercap-mcp` | `go install bettercap` fails — upstream dependency |
| `gitleaks-mcp` | Build error in upstream source |
| `horusec-mcp` | Horusec install script returns exit 127 |
| `subjack-mcp` | Requires Go ≥ 1.25.1, base image uses 1.24 |
| `vulnerability-scanner-mcp` | Missing `requirements.txt` in upstream repo |
| `x8-mcp` | References non-existent base image `x8-builder:latest` |

All other 380 servers build and run successfully.

---

## Resource Guidelines

| Containers running | Recommended RAM | Recommended CPUs |
|-------------------|-----------------|------------------|
| Infra only (3) | 2 GB | 2 |
| Infra + 50 servers | 4 GB | 4 |
| Infra + 200 servers | 8 GB | 6 |
| Full farm (386) | 16 GB+ | 8+ |

Servers are set to `restart: 'no'` — they only run when explicitly started. Start only what you need to avoid overloading Docker Desktop.
