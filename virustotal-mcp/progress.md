# VirusTotal MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`virustotal-mcp/`)
- [x] Create `requirements.txt` with fastmcp and requests dependencies
- [x] Create `mcp_server.py` with FastMCP server querying VirusTotal API v3
  - [x] `vt_file_report` tool — GET /api/v3/files/{hash}
  - [x] `vt_url_report` tool — GET /api/v3/urls/{base64_url_id}
  - [x] `vt_domain_report` tool — GET /api/v3/domains/{domain}
  - [x] `vt_ip_report` tool — GET /api/v3/ip_addresses/{ip}
  - [x] `vt_scan_url` tool — POST /api/v3/urls (submit for scanning)
  - [x] `vt_get_analysis` tool — GET /api/v3/analyses/{id}
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling (401, 404, timeouts)
  - [x] Threat verdict calculation from last_analysis_stats
- [x] Create `Dockerfile` — python:3.12-slim-bookworm, tini, mcpuser
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8369
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8369** — VirusTotal MCP Server (streamable-http)

## Notes

- API-based server — queries VirusTotal REST API v3 directly (no CLI binary)
- Requires VT_API_KEY environment variable (get at https://www.virustotal.com)
- Uses `requests` library for HTTP calls
- Threat verdict computed from last_analysis_stats: malicious (>=5 detections), suspicious (>=1 malicious or >=3 suspicious), clean
- URL lookups use base64-encoded URL IDs per VT API v3 spec
