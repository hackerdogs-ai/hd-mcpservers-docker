# MISP MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`misp-mcp/`)
- [x] Create `requirements.txt` with fastmcp and requests dependencies
- [x] Create `mcp_server.py` with FastMCP server querying MISP REST API
  - [x] `misp_search_attributes` tool — search IOCs by value
  - [x] `misp_search_events` tool — search events by keyword
  - [x] `misp_get_event` tool — get event details by ID
  - [x] `misp_add_attribute` tool — add attribute to event
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling (401, 403, 404, timeouts, connection errors)
  - [x] SSL verification disabled (self-signed cert support)
- [x] Create `Dockerfile` with python:3.12-slim-bookworm, tini, mcpuser
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8371, MISP_API_KEY and MISP_URL pass-through
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8371** — MISP MCP Server (streamable-http)

## Notes

- Source: https://www.misp-project.org/
- API-based server — uses `requests` to query MISP REST API (no CLI binary)
- Requires `MISP_API_KEY` and `MISP_URL` environment variables
- SSL verification disabled (`verify=False`) for self-signed certificate support
- 4 tools: search attributes, search events, get event, add attribute
