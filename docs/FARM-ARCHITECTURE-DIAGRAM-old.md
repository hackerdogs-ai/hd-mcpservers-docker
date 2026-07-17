> **SUPERSEDED.** Canonical design & roadmap: [`AI-aware-zero-trust-gateway-for-MCP.md`](./AI-aware-zero-trust-gateway-for-MCP.md). This file is archived historical material.

# Hackerdogs MCP Server Farm — Architecture Diagram & Description

**Version:** 1.0
**Date:** 2026-04-02
**Servers:** 386
**Entry Point:** mcp.hackerdogs.ai

---

## Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                         HACKERDOGS MCP SERVER FARM — ARCHITECTURE                           ║
║                              mcp.hackerdogs.ai  |  386 Servers                             ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝

  ┌─────────────────────────────────────────────────────────────────────────────────────────┐
  │  CLIENTS                                                                                │
  │                                                                                         │
  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐               │
  │  │   Claude /  │   │  Cursor /   │   │  OpenAI     │   │   Custom    │               │
  │  │   Claude    │   │  Windsurf   │   │  Agents     │   │   Scripts   │               │
  │  │   Desktop   │   │             │   │             │   │   / CI      │               │
  │  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘               │
  │         └─────────────────┴─────────────────┴─────────────────┘                       │
  │                                     │                                                  │
  │               HTTPS + Bearer Token (hd_sk_...)  +  Optional X-API-KEY headers         │
  └─────────────────────────────────────┼───────────────────────────────────────────────────┘
                                        │
                                        ▼
  ┌─────────────────────────────────────────────────────────────────────────────────────────┐
  │  CLOUDFLARE EDGE  —  mcp.hackerdogs.ai                                                  │
  │                                                                                         │
  │  • TLS termination (HTTPS → HTTP internally)                                            │
  │  • DDoS protection                                                                      │
  │  • Real server IP never exposed                                                         │
  └─────────────────────────────────────┼───────────────────────────────────────────────────┘
                                        │
                              Encrypted outbound tunnel
                              (no open inbound ports)
                                        │
╔═══════════════════════════════════════▼═══════════════════════════════════════════════════╗
║  HOST MACHINE  (Ubuntu/Linux  |  32GB RAM  |  8 CPU  |  500GB SSD)                       ║
║  Docker Network: mcpfarm_internal  (bridge, isolated)                                    ║
║                                                                                           ║
║  ┌─────────────────────────────────────────────────────────────────────────────────────┐ ║
║  │  INFRASTRUCTURE LAYER                                                               │ ║
║  │                                                                                     │ ║
║  │  ┌──────────────────┐    ┌──────────────────────┐    ┌────────────────────────┐   │ ║
║  │  │  cloudflared     │    │        Caddy          │    │     auth-gateway       │   │ ║
║  │  │                  │    │   (Reverse Proxy)     │    │     (FastAPI)          │   │ ║
║  │  │  Cloudflare      │───▶│                       │    │                        │   │ ║
║  │  │  tunnel client   │    │  • URL routing        │───▶│  • Token verification  │   │ ║
║  │  │                  │    │  • forward_auth       │    │  • Admin REST API      │   │ ║
║  │  │  TUNNEL_TOKEN    │    │  • path stripping     │    │  • Health monitoring   │   │ ║
║  │  │  from .env       │    │  • hot-reload         │    │  • Rate limiting       │   │ ║
║  │  │                  │    │    routes.conf        │    │  • Audit logging       │   │ ║
║  │  │  :80 (internal)  │    │                       │    │  • Dynamic server mgmt │   │ ║
║  │  └──────────────────┘    │  :80 (internal only)  │    │                        │   │ ║
║  │                          └──────────┬────────────┘    │  :9090 (internal only) │   │ ║
║  │                                     │                 └──────────┬─────────────┘   │ ║
║  │                                     │                            │                  │ ║
║  │                          ┌──────────┤ shared volume              │                  │ ║
║  │                          │caddy_    │ (routes.conf)         ┌────┴──────────────┐  │ ║
║  │                          │routes    │                        │   SQLite DB       │  │ ║
║  │                          └──────────┤                        │   (WAL mode)      │  │ ║
║  │                                     │                        │                   │  │ ║
║  │                                     │                        │  api_keys         │  │ ║
║  │                                     │                        │  servers          │  │ ║
║  │                                     │                        │  request_log      │  │ ║
║  │                                     │                        │                   │  │ ║
║  │                                     │                        │  auth_data volume │  │ ║
║  │                                     │                        └───────────────────┘  │ ║
║  └─────────────────────────────────────┼─────────────────────────────────────────────┘ ║
║                                        │                                                 ║
║                         Routes to one of 386 MCP servers                                ║
║                                        │                                                 ║
║  ┌─────────────────────────────────────▼─────────────────────────────────────────────┐  ║
║  │  MCP SERVER LAYER  (386 containers — no host ports, internal network only)        │  ║
║  │                                                                                   │  ║
║  │  ┌────────────────────────────────────────────────────────────────────────────┐  │  ║
║  │  │  NETWORK RECON          VULN SCANNING        WEB APP TESTING               │  │  ║
║  │  │  ──────────────         ─────────────         ─────────────────            │  │  ║
║  │  │  nmap-mcp               trivy-mcp             sqlmap-mcp                  │  │  ║
║  │  │  naabu-mcp              nuclei-mcp            dalfox-mcp                  │  │  ║
║  │  │  rustscan-mcp           nikto-mcp             xsstrike-mcp                │  │  ║
║  │  │  masscan-mcp            openvas-mcp           wfuzz-mcp                   │  │  ║
║  │  │  zmap-mcp               grype-mcp             ffuf-mcp                    │  │  ║
║  │  │  fping-mcp              semgrep-mcp           dirb-mcp                    │  │  ║
║  │  │  ...                    ...                   ...                         │  │  ║
║  │  ├────────────────────────────────────────────────────────────────────────────┤  │  ║
║  │  │  OSINT                  EXPLOITATION          CLOUD / CONTAINER            │  │  ║
║  │  │  ──────                 ────────────          ─────────────────            │  │  ║
║  │  │  sherlock-mcp           metasploit-mcp        kube-hunter-mcp             │  │  ║
║  │  │  maigret-mcp            hydra-mcp             checkov-mcp                 │  │  ║
║  │  │  spiderfoot-mcp         john-mcp              trivy-security-mcp          │  │  ║
║  │  │  theharvester-mcp       hashcat-mcp           kubescape-mcp               │  │  ║
║  │  │  ghunt-mcp              sqlmap-mcp            scoutsuite-mcp              │  │  ║
║  │  │  ...                    ...                   ...                         │  │  ║
║  │  ├────────────────────────────────────────────────────────────────────────────┤  │  ║
║  │  │  BINARY / RE            NETWORK ATTACKS       MISC / DATA                 │  │  ║
║  │  │  ────────────           ───────────────       ──────────────               │  │  ║
║  │  │  ghidra-mcp             bettercap-mcp         virustotal-mcp              │  │  ║
║  │  │  radare2-mcp            ettercap-mcp          shodan-mcp                  │  │  ║
║  │  │  binwalk-mcp            responder-mcp         notion-mcp                  │  │  ║
║  │  │  cutter-mcp             wifiphisher-mcp       slack-mcp                   │  │  ║
║  │  │  ...                    ...                   ...  (386 total)            │  │  ║
║  │  └────────────────────────────────────────────────────────────────────────────┘  │  ║
║  │                                                                                   │  ║
║  │  Each container:  hackerdogs/<name>:latest  |  MCP_TRANSPORT=streamable-http     │  ║
║  │                   Non-root user  |  tini init  |  Port 8100–8699 (internal)      │  ║
║  └───────────────────────────────────────────────────────────────────────────────────┘  ║
╚═══════════════════════════════════════════════════════════════════════════════════════════╝


  REQUEST FLOW
  ─────────────────────────────────────────────────────────────────────────────────────
  1.  Client  →  POST https://mcp.hackerdogs.ai/nmap-mcp/mcp/
                 Authorization: Bearer hd_sk_abc123
                 X-SHODAN-API-KEY: user_key   (optional, per-tool)

  2.  Cloudflare Edge  →  cloudflared (tunnel)  →  Caddy :80

  3.  Caddy  →  forward_auth  →  auth-gateway:9090/verify
                ✓ Token valid?   ✓ Active?   ✓ Scoped?   ✓ Rate limit OK?
                200 = proceed    401/403 = reject (request dies here)

  4.  Caddy  →  strips /nmap-mcp prefix  →  reverse_proxy nmap-mcp:8140

  5.  nmap-mcp  →  extracts X-* headers  →  injects as env vars (per-request)
                →  runs nmap subprocess  →  returns JSON-RPC result

  6.  Response travels back:  nmap-mcp → Caddy → cloudflared → Cloudflare → Client


  URL SCHEME
  ─────────────────────────────────────────────────────────────────────────────────────
  https://mcp.hackerdogs.ai/{server-name}/mcp/

  Examples:
    https://mcp.hackerdogs.ai/nmap-mcp/mcp/
    https://mcp.hackerdogs.ai/metasploit-mcp/mcp/
    https://mcp.hackerdogs.ai/trivy-mcp/mcp/


  ADMIN API  (no UI — all curl)
  ─────────────────────────────────────────────────────────────────────────────────────
  POST   /admin/keys                  Create API key
  GET    /admin/keys                  List all keys
  PATCH  /admin/keys/{id}             Revoke / update scope / rate limit
  POST   /admin/servers               Register new server (hot, no restart)
  GET    /admin/servers               List all 386 servers + health status
  GET    /admin/audit                 Query request log
  GET    /services                    Public — all servers + health (no auth)
  GET    /health                      Farm liveness check


  PORT ALLOCATION  (internal Docker network only)
  ─────────────────────────────────────────────────────────────────────────────────────
  8100–8199   Core tools + network recon
  8200–8299   Vulnerability scanning + web app testing
  8300–8399   OSINT + exploitation
  8400–8499   Cloud / container + binary / RE
  8500–8599   Network attacks + misc
  8600–8699   AWS / Azure / cloud provider tools
  8700–8799   ★ Reserved — dynamic servers (added via admin API at runtime)


  SECURITY LAYERS
  ─────────────────────────────────────────────────────────────────────────────────────
  Layer 0  Host            No open inbound ports. cloudflared is outbound-only.
  Layer 1  Network         Private Docker bridge. MCP servers unreachable from internet.
  Layer 2  TLS             Cloudflare terminates HTTPS. Internal traffic is plaintext.
  Layer 3  AuthN           SHA-256 Bearer token checked on every request via forward_auth.
  Layer 4  AuthZ           Per-key scopes, rate limits, expiry enforced by auth-gateway.
  Layer 5  Container       Non-root user, no shared state, tini init, stateless.
  Layer 6  LLM Guard       PolicyLayer Intercept (recommended) — tool-call firewall.
```

---

## Detailed Description

### The Big Picture

The diagram shows a **layered system** that sits between AI clients on the internet and 386 security tools running in Docker containers on a single machine. Traffic flows top-to-bottom through several distinct layers, each with a specific job. Nothing in the bottom layers is ever directly reachable from the internet.

---

### Layer 1 — Clients

The top row shows who connects to the farm. These are the consumers:

- **Claude / Claude Desktop** — Anthropic's AI assistant configured with MCP server URLs
- **Cursor / Windsurf** — AI-powered code editors that support MCP
- **OpenAI Agents** — Any agent built on OpenAI's SDK that speaks the MCP protocol
- **Custom Scripts / CI** — Automation pipelines, pentesting scripts, or any HTTP client

All of them connect the same way — they send an HTTP POST request to a URL like `https://mcp.hackerdogs.ai/nmap-mcp/mcp/` with two things in the headers:
1. A **Bearer token** (`hd_sk_abc123...`) which is their farm access credential
2. Optionally, **X- prefixed API keys** for tools that need third-party services (e.g. `X-SHODAN-API-KEY`)

From the client's perspective, this looks identical to any other MCP server. They don't know anything about the farm, the proxy, or the authentication layer behind it.

---

### Layer 2 — Cloudflare Edge

Before traffic reaches your machine at all, it hits **Cloudflare's global edge network**. Cloudflare owns the DNS record for `mcp.hackerdogs.ai` and does three things here:

- **TLS termination** — the client's HTTPS connection ends here. Traffic from Cloudflare to your machine travels inside an encrypted tunnel, so there's no certificate to manage on your server.
- **DDoS protection** — Cloudflare absorbs volumetric attacks before they reach your machine.
- **IP hiding** — your server's real IP address is never revealed to clients. They only ever see Cloudflare's IP.

This layer uses Cloudflare's free tier — no additional cost.

---

### Layer 3 — Cloudflare Tunnel (cloudflared container)

This is one of the most important design decisions in the whole architecture. Instead of opening a port on your machine and waiting for connections to arrive, the `cloudflared` container **dials outward** to Cloudflare's network and creates a persistent encrypted tunnel. Cloudflare then pushes inbound traffic down that tunnel to your machine.

**Why this matters:**
- Your machine has **zero open inbound ports** — a port scanner hitting your IP would find nothing
- No firewall rules to configure on your router or host
- Your real IP address is completely hidden
- The `TUNNEL_TOKEN` in your `.env` file is what authenticates this connection to Cloudflare

The cloudflared container receives traffic from Cloudflare and forwards it to `caddy:80` on the internal Docker network.

---

### Layer 4 — Caddy (The Receptionist)

Caddy is the **single entry point for all 386 MCP servers**. Every request that comes through the tunnel hits Caddy first. It does three things:

**1. URL routing** — Caddy reads the URL path to figure out which MCP server the request is for. A request to `/nmap-mcp/mcp/` is destined for the nmap container. A request to `/metasploit-mcp/mcp/` is destined for metasploit. Caddy knows all 386 routes because they are listed in a file called `routes.conf` that the generator script creates automatically.

**2. Authentication delegation (forward_auth)** — Before Caddy forwards any request to an MCP server, it calls the auth-gateway and asks "is this person allowed in?" It passes the Bearer token to the auth-gateway and waits for a yes or no. If the answer is no, Caddy rejects the request right here — the MCP server never even sees it.

**3. Path stripping** — Once a request is authenticated, Caddy strips the server-name prefix from the URL. So `/nmap-mcp/mcp/` becomes just `/mcp/` before it reaches the nmap container. The MCP server doesn't need to know it's sitting behind a proxy.

**Hot-reload** — Caddy has a built-in admin API on port 2019. When a new server is registered at runtime, the auth-gateway rewrites `routes.conf` and tells Caddy to reload it instantly — no downtime, no restart.

---

### Layer 5 — Auth Gateway (The Bouncer)

The auth-gateway is a small **FastAPI Python service** that is the brain of the entire farm. It has two roles:

**Role 1: Token verification (called by Caddy on every single request)**

When Caddy calls `/verify`, the auth-gateway runs through a checklist in order:
1. Does this token exist in the database? (SHA-256 hash lookup — ~0.01ms)
2. Is it marked as active?
3. Has it expired?
4. Does its scope include the server being accessed?
5. Has it exceeded its rate limit (requests per minute)?

If any check fails, it returns a 401 or 403 and the request is dead. If all pass, it logs the request and returns 200.

**Role 2: Admin REST API (all farm management)**

There is no web UI anywhere in this system. Everything is managed through API calls:
- Create / revoke / update API keys
- Register new MCP servers at runtime (hot, no compose restart needed)
- View health status of all 386 servers
- Query the audit log (who called what and when)
- Get farm-wide statistics

The auth-gateway also runs a **background health check loop** — every 30 seconds it sends a request to every MCP server's `/mcp/` endpoint and records whether it's healthy. This data feeds the public `/services` endpoint.

**Docker socket access** — The auth-gateway is the only container that mounts the Docker socket. This gives it the ability to create, start, stop, and remove containers at runtime, which powers the dynamic server registration feature.

---

### The SQLite Database

Sitting alongside the auth-gateway is a **single SQLite file** on a Docker volume. This is the only persistent state in the entire farm. It contains three tables:

- **api_keys** — every issued Bearer token (stored as a SHA-256 hash, never in plaintext), with its owner, scopes, rate limit, and expiry
- **servers** — a registry of all 386 MCP servers (name, image, port, health status, whether it's static or dynamic)
- **request_log** — every authenticated request that came through (which key, which server, timestamp, response status, latency)

SQLite is used instead of Postgres or Redis because it needs no extra container, handles thousands of concurrent reads with WAL mode, and the entire database state is a single file that can be backed up with one copy command.

---

### The Shared Volume (caddy_routes)

There's a shared Docker volume called `caddy_routes` that sits between Caddy and the auth-gateway. This is how live route updates work:

- The auth-gateway writes `routes.conf` to this volume when servers are added or removed
- Caddy reads `routes.conf` from this volume on every reload
- When the auth-gateway calls Caddy's admin API to reload, Caddy picks up the new file immediately

This enables zero-downtime dynamic server registration — no compose restart, no config file editing, no manual intervention.

---

### Layer 6 — The MCP Server Layer (386 Containers)

At the bottom are the 386 security tool containers. These are completely isolated from the internet and from each other. They live entirely on the internal Docker bridge network and are only reachable through Caddy.

The servers are grouped into eight categories:

| Category | Examples |
|----------|---------|
| **Network Recon** | nmap, naabu, rustscan, masscan, zmap, fping |
| **Vulnerability Scanning** | trivy, nuclei, nikto, openvas, grype, semgrep |
| **Web App Testing** | sqlmap, dalfox, xsstrike, wfuzz, ffuf, dirb |
| **OSINT** | sherlock, maigret, spiderfoot, theharvester, ghunt |
| **Exploitation / Post-exploit** | metasploit, hydra, john, hashcat |
| **Cloud / Container** | kube-hunter, checkov, kubescape, scoutsuite |
| **Binary / Reverse Engineering** | ghidra, radare2, binwalk, cutter |
| **Network Attacks / Wireless** | bettercap, ettercap, responder, wifiphisher |

**Every container shares the same structure:**
- Built from `hackerdogs/<name>:latest` on Docker Hub
- Runs as a non-root user
- Uses `tini` as the init process for clean signal handling
- Exposes a single `/mcp/` endpoint over HTTP (no host port binding)
- Stateless — no data written between requests
- Runs with `MCP_TRANSPORT=streamable-http` so it speaks the HTTP streamable MCP protocol

**Upstream API key injection** — when a request arrives with an `X-SHODAN-API-KEY` header, the MCP server middleware picks it up and injects it as an environment variable into the subprocess that runs the actual tool. Python's `contextvars` ensures that two concurrent requests from different users with different API keys never interfere with each other. The key exists only for the duration of that one request and is never stored anywhere.

---

### The Request Flow End-to-End

Putting it all together, here is what happens in under 50ms from the moment a tool is called:

```
1. Agent sends:
   POST https://mcp.hackerdogs.ai/nmap-mcp/mcp/
   Authorization: Bearer hd_sk_abc123
   Body: {"method": "tools/call", "params": {"name": "run_nmap", ...}}

2. Cloudflare receives it, terminates TLS, pushes it down the tunnel.

3. cloudflared receives it, forwards to caddy:80.

4. Caddy matches /nmap-mcp/* → calls auth-gateway:9090/verify.
   auth-gateway: token ✓  active ✓  not expired ✓  scoped ✓  rate limit ✓  → 200 OK
   (Any check fails → 401/403 returned to client, request ends here.)

5. Caddy strips /nmap-mcp, proxies request to nmap-mcp:8140/mcp/

6. nmap-mcp extracts X-* headers, injects as per-request env vars.
   Runs nmap subprocess, returns scan results as JSON-RPC response.

7. Response travels back: nmap-mcp → Caddy → cloudflared → Cloudflare → agent.
```

---

### What Makes This Architecture Powerful

The entire system has **one operational command** — `docker compose up -d`. Everything else is API calls. You can:

- Add a new server without restarting anything
- Revoke a compromised token in milliseconds
- Inspect exactly who called what tool and when
- Scale from 10 servers to 386 by changing one JSON file and re-running the generator
- Replace any MCP server by updating its Docker image and restarting one container

The farm operator controls everything. The users just see a standard MCP URL.
