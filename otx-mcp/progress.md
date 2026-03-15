# AlienVault OTX MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`otx-mcp/`)
- [x] Create `requirements.txt` with fastmcp and OTXv2 dependencies
- [x] Create `mcp_server.py` with FastMCP server using OTXv2 Python SDK
  - [x] `otx_file_report` tool — query OTX for file hash (MD5/SHA1/SHA256)
  - [x] `otx_url_report` tool — query OTX for URL
  - [x] `otx_domain_report` tool — query OTX for domain
  - [x] `otx_ip_report` tool — query OTX for IP address
  - [x] `otx_submit_url` tool — submit URL to OTX for analysis
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling (InvalidAPIKey, NotFound, timeouts)
- [x] Create `Dockerfile` — python:3.12-slim-bookworm with OTXv2 pip install
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8368
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8368** — AlienVault OTX MCP Server (streamable-http)

## Notes

- API-based server using OTXv2 Python SDK (no CLI binary)
- Requires OTX_API_KEY environment variable (free at https://otx.alienvault.com)
- 5 tools for threat intelligence lookups (file hash, URL, domain, IP, submit URL)
