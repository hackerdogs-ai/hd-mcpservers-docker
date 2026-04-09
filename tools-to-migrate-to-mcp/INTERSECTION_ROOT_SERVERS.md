# Acuvity/Cyproxio intersection — root MCP server folders

All MCP servers in the Acuvity/Cyproxio intersection must live at **repo root** as `{tool}-mcp/` (like every other MCP server). Each folder must be **Hackerdogs compliant**: no Minibridge, stdio + streamable-http via FastMCP only.

---

## Per-server checklist (root folder)

Each `{tool}-mcp/` at repo root must have:

| Item | Required | Notes |
|------|----------|--------|
| **Dockerfile** | Yes | No Minibridge; install CLI (or API-only); Python 3.11+; non-root user; `MCP_TRANSPORT` default stdio, `MCP_PORT` set |
| **mcp_server.py** | Yes | FastMCP; `MCP_TRANSPORT` / `MCP_PORT`; stdio and streamable-http; tool(s) matching Cyproxio semantics |
| **requirements.txt** | Yes | `fastmcp>=0.1.0` (+ httpx etc. if needed) |
| **README.md** | Yes | Hackerdogs logo; tools; Docker (stdio + HTTP); mcpServer.json snippet; “no Minibridge” |
| **mcpServer.json** | Yes | Points to `hackerdogs/{tool}-mcp:latest` (or local build); env `MCP_TRANSPORT`, `MCP_PORT` |
| **test.sh** | Yes | All 5 steps: (1) install, (2) stdio tools/list, (3) stdio tools/call, (4) HTTP tools/list, (5) HTTP tools/call |
| **docker-compose.yml** | Optional | Port mapping for streamable-http |
| **publish_to_hackerdogs.sh** | Optional | Build/publish script |

---

## Status: intersection servers

### Already at root (Hackerdogs-built, verify only)

| Root folder | Port | Minibridge? | Streamable-http? | Action |
|-------------|------|-------------|------------------|--------|
| commix-mcp | 8225 | No | Yes | Verify test.sh 5-step; README/mcpServer point to hackerdogs |
| scoutsuite-mcp | (see dir) | No | Yes | Same |
| sslscan-mcp | (see dir) | No | Yes | Same |
| smuggler-mcp | (see dir) | No | Yes | Same |
| wpscan-mcp | (see dir) | No | Yes | Same |

### Created at root (Hackerdogs, no Minibridge)

| Root folder | Port | Notes |
|-------------|------|--------|
| **alterx-mcp** | 8380 | do_alterx(domain, pattern, output_file_path?) |
| **crtsh-mcp** | 8381 | crt.sh API only; crtsh(target) |
| **amass-mcp** | 8382 | run_amass(arguments) — OWASP Amass |
| **arjun-mcp** | 8383 | do_arjun(arguments) — Arjun HTTP params |

### Created at root (remaining 14)

| Root folder | Port | Install |
|-------------|------|--------|
| assetfinder-mcp | 8384 | Go: tomnomnom/assetfinder |
| ffuf-mcp | 8385 | Go: ffuf/ffuf |
| httpx-mcp | 8386 | Go: projectdiscovery/httpx |
| katana-mcp | 8387 | Go: projectdiscovery/katana |
| masscan-mcp | 8388 | apt: masscan |
| mobsf-mcp | 8389 | TBD (Python-only image for now) |
| nmap-mcp | 8390 | apt: nmap |
| nuclei-mcp | 8391 | Go: projectdiscovery/nuclei |
| http-headers-security-mcp | 8392 | TBD (Python-only for now) |
| shuffledns-mcp | 8393 | Go: projectdiscovery/shuffledns |
| sqlmap-mcp | 8394 | apt: sqlmap |
| waybackurls-mcp | 8395 | Go: tomnomnom/waybackurls |
| cero-mcp | 8396 | Go: glebarez/cero |
| gowitness-mcp | 8397 | Go: sensepost/gowitness |

(Reserve 8380–8399.)

---

## Config-only “acuvity-mcp-server-*” dirs

`acuvity-mcp-server-alterx-mcp`, `acuvity-mcp-server-amass-mcp`, etc. currently point to **acuvity/*** images (Minibridge). Option: update their README and mcpServer.json to use **hackerdogs/alterx-mcp**, **hackerdogs/amass-mcp**, etc., and state “Hackerdogs build; no Minibridge.” The canonical server is then the root folder `alterx-mcp`, `amass-mcp`, etc.
