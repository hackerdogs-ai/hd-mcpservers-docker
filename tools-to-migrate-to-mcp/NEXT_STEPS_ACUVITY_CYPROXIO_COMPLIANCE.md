# Next Steps: Acuvity/Cyproxio → Hackerdogs Compliant (No Minibridge)

**Goal:** Ensure all required MCP servers and their artifacts live in the Hackerdogs repo, are Hackerdogs compliant, and **do not depend on Minibridge**. HTTP streamable must be provided by **FastMCP’s native `streamable-http`** transport only.

**Minibridge (reviewed):** Local copy at `tools-to-migrate-to-mcp/acuvity/minibridge-main`. Minibridge is a Go frontend–backend bridge: the frontend exposes HTTP endpoints (`/mcp`, `/sse`, `/message` on port 8000 by default); the backend runs the real MCP server (e.g. Cyproxio Node) as a subprocess over **stdio** only. So Acuvity images = Minibridge process + stdio child (no HTTP in the child). We remove this dependency by using a single process per server: FastMCP (Python) with both stdio and streamable-http built in. See **ACUVITY_CYPROXIO_AUDIT.md** §6 for the full Minibridge code review.

---

## 1. Strategy (No Minibridge)

| Source | What we do |
|--------|------------|
| **Acuvity images** (`acuvity/mcp-server-*`) | Do **not** use as primary runtime. They rely on Minibridge for HTTP/SSE. |
| **Cyproxio source** (`cyproxio/mcp-for-security-main`) | Use as **reference** for tool names, parameters, and CLI invocations. |
| **Hackerdogs servers** | Each server is a **FastMCP (Python)** wrapper that runs the same CLI tools as Cyproxio, with **stdio + streamable-http** via `MCP_TRANSPORT` / `MCP_PORT`. No Minibridge. |

**Artifacts per server (all under repo root `{tool}-mcp/`):**

- `mcp_server.py` — FastMCP, `MCP_TRANSPORT` (stdio | streamable-http), `MCP_PORT`
- `Dockerfile` — Python 3.11+ slim, install CLI tool + deps, **no Minibridge**
- `README.md` — Hackerdogs branding, both transports, env vars, tools reference
- `mcpServer.json` — Cursor/Claude config using **hackerdogs/** image (or local docker run)
- `test.sh` — Full compliance: install, stdio tools/list, stdio tools/call, HTTP tools/list, HTTP tools/call
- `requirements.txt` — `fastmcp` (pinned)
- `docker-compose.yml` — Optional; port mapping for streamable-http
- `publish_to_hackerdogs.sh` — Build/publish to Hackerdogs registry

---

## 2. Servers to Handle (from ACUVITY_CYPROXIO_AUDIT.md)

### 2.1 Already Hackerdogs-built (5) — Verify only

| Dir | Port | Action |
|-----|------|--------|
| **commix-mcp** | 8225 | Verify: no acuvity/minibridge refs; test.sh has all 5 steps; streamable-http works. |
| **scoutsuite-mcp** | (check) | Same. |
| **sslscan-mcp** | (check) | Same. |
| **smuggler-mcp** | (check) | Same. |
| **wpscan-mcp** | (check) | Same. |

**Checklist per server:** README/mcpServer.json point to `hackerdogs/*` (or local build); no `acuvity/*` as default; `test.sh` includes (1) install, (2) stdio tools/list, (3) stdio tools/call, (4) HTTP tools/list, (5) HTTP tools/call.

---

### 2.2 Need new Hackerdogs dir (18 from Cyproxio + 2 Cyproxio-only)

Create a **new** `{tool}-mcp/` for each. Implement FastMCP in Python that shells out to the same CLI as Cyproxio. Assign a unique port (see root README reserved range).

| # | Tool | New dir | Cyproxio source path | Notes |
|---|------|---------|----------------------|-------|
| 1 | alterx | **alterx-mcp** | `cyproxio/.../alterx-mcp` | Pattern-based wordlist for subdomains |
| 2 | amass | **amass-mcp** | `cyproxio/.../amass-mcp` | Subdomain enum |
| 3 | arjun | **arjun-mcp** | `cyproxio/.../arjun-mcp` | HTTP param discovery |
| 4 | assetfinder | **assetfinder-mcp** | `cyproxio/.../assetfinder-mcp` | Passive subdomain discovery |
| 5 | crtsh | **crtsh-mcp** | `cyproxio/.../crtsh-mcp` | crt.sh cert search |
| 6 | ffuf | **ffuf-mcp** | `cyproxio/.../ffuf-mcp` | Web fuzzer |
| 7 | httpx | **httpx-mcp** | `cyproxio/.../httpx-mcp` | HTTP toolkit |
| 8 | katana | **katana-mcp** | `cyproxio/.../katana-mcp` | Web crawler |
| 9 | masscan | **masscan-mcp** | `cyproxio/.../masscan-mcp` | Port scanner |
| 10 | mobsf | **mobsf-mcp** | `cyproxio/.../mobsf-mcp` | Mobile security (may need API) |
| 11 | nmap | **nmap-mcp** | `cyproxio/.../nmap-mcp` | Network scanner |
| 12 | nuclei | **nuclei-mcp** | `cyproxio/.../nuclei-mcp` | Vuln scanner |
| 13 | http-headers-security | **http-headers-security-mcp** or **oshp-mcp** | `cyproxio/.../http-headers-security-mcp` | OWASP headers |
| 14 | shuffledns | **shuffledns-mcp** | `cyproxio/.../shuffledns-mcp` | DNS brute-force |
| 15 | sqlmap | **sqlmap-mcp** | `cyproxio/.../sqlmap-mcp` | SQL injection |
| 16 | waybackurls | **waybackurls-mcp** | `cyproxio/.../waybackurls-mcp` | Wayback URLs |
| 17 | cero | **cero-mcp** | `cyproxio/.../cero` | Cert-based subdomain enum |
| 18 | gowitness | **gowitness-mcp** | `cyproxio/.../gowitness-mcp` | Screenshot/recon |

**Per server:** Copy behavior from Cyproxio `src/index.ts` (tool names, args, CLI calls) → implement in `mcp_server.py` with subprocess + FastMCP; add Dockerfile (install binary + Python); add README, mcpServer.json, test.sh, requirements.txt. **Do not** use Acuvity Dockerfile or Minibridge.

---

### 2.3 Config-only “acuvity-mcp-server-*” dirs (Phase 2 first 5)

These currently point to **acuvity/*** images (Minibridge). Two options:

**Option A (recommended):** Replace with Hackerdogs-built servers and remove Minibridge.

- **alterx:** Create **alterx-mcp** (as above). Then either (i) remove `acuvity-mcp-server-alterx-mcp` and use `alterx-mcp` everywhere, or (ii) make `acuvity-mcp-server-alterx-mcp` a thin config that points to `hackerdogs/alterx-mcp` and states “Hackerdogs build; no Minibridge.”
- **amass, arjun, assetfinder:** Same — add **amass-mcp**, **arjun-mcp**, **assetfinder-mcp**; then point config to hackerdogs images.
- **atlas-docs:** Not Cyproxio; keep as optional upstream reference or add a separate Hackerdogs build later.

**Option B (temporary):** Keep acuvity-mcp-server-* as optional “upstream” in README only; primary path is always a Hackerdogs `*-mcp` server (no Minibridge in our artifacts).

---

## 3. Order of Work

1. **Verify the 5 existing** (commix, scoutsuite, sslscan, smuggler, wpscan): no Minibridge; full test.sh; README/mcpServer point to hackerdogs.
2. **Created at root:** **alterx-mcp** (8380) and **crtsh-mcp** (8381) are done as the template — FastMCP, no Minibridge, stdio + streamable-http, full test.sh. See **INTERSECTION_ROOT_SERVERS.md** for the checklist and status.
3. **Roll out the remaining 16** from the table in §2.2 using the same pattern (amass-mcp, arjun-mcp, assetfinder-mcp, ffuf-mcp, httpx-mcp, katana-mcp, masscan-mcp, mobsf-mcp, nmap-mcp, nuclei-mcp, http-headers-security-mcp, shuffledns-mcp, sqlmap-mcp, waybackurls-mcp, cero-mcp, gowitness-mcp).
4. **Switch config-only dirs** (acuvity-mcp-server-alterx-mcp, etc.) to point to **hackerdogs/** images and document “no Minibridge” in README.
5. **Root README:** Update tool/port table so every Cyproxio-related server has one entry pointing to our image and port.

---

## 4. Copying “Artifacts” — What Actually Gets Copied

- **From Cyproxio:** Tool names, parameter names, CLI commands (e.g. `alterx -d domain -p pattern`). Implement this in Python (FastMCP + subprocess). Do **not** copy Node/TS or Acuvity Dockerfile.
- **From Acuvity:** Only **documentation** (e.g. tool descriptions, example prompts) if useful. Do **not** copy Minibridge, Helm charts, or Acuvity Dockerfile.
- **Into Hackerdogs:** Only Hackerdogs-style artifacts: `mcp_server.py`, `Dockerfile`, `README.md`, `mcpServer.json`, `test.sh`, `requirements.txt`, etc., all using **FastMCP + streamable-http**, no Minibridge.

---

## 5. Removing Minibridge — Checklist

Removing Minibridge means we do **not** run Acuvity’s container (which starts `minibridge aio -- node ...`). Our containers run only the Hackerdogs server process (e.g. `python mcp_server.py` with FastMCP).

- [ ] No server in repo uses `acuvity/*` image as **default** in its own `mcpServer.json` or README “Docker Run” for production.
- [ ] Every server that we “own” has a **Dockerfile in repo** that builds an image with FastMCP and **no** Minibridge binary or entrypoint.
- [ ] Every such server supports **streamable-http** via `MCP_TRANSPORT=streamable-http` and `MCP_PORT` (FastMCP native transport).
- [ ] `test.sh` for each server includes HTTP streamable tests (tools/list and tools/call) with `Accept: application/json, text/event-stream`.
- [ ] Root README and any “Phase 2” doc state that Hackerdogs builds are Minibridge-free and use FastMCP streamable-http.

---

## 6. Summary

| Step | Description |
|------|-------------|
| 1 | Verify 5 existing Hackerdogs servers (commix, scoutsuite, sslscan, smuggler, wpscan): compliant, no Minibridge. |
| 2 | Add 18 new `{tool}-mcp` dirs from Cyproxio (alterx, amass, arjun, assetfinder, crtsh, ffuf, httpx, katana, masscan, mobsf, nmap, nuclei, oshp, shuffledns, sqlmap, waybackurls, cero, gowitness) with FastMCP + Dockerfile + test.sh. |
| 3 | Point acuvity-mcp-server-* config dirs to hackerdogs images (or replace by tool-named dirs) and document “no Minibridge.” |
| 4 | Update root README and port table; ensure no default use of Acuvity/Minibridge. |

Result: **all required MCP servers and artifacts are in the Hackerdogs directory, Hackerdogs compliant, and Minibridge is removed from our stack.**
