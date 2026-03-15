# OpenCTI MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`opencti-mcp/`)
- [x] Create `requirements.txt` with fastmcp and pycti dependencies
- [x] Create `mcp_server.py` with FastMCP server using pycti API client
  - [x] `opencti_search_indicators` tool — search IOCs
  - [x] `opencti_search_malware` tool — search malware entries
  - [x] `opencti_search_threat_actors` tool — search threat actors
  - [x] `opencti_get_report` tool — get or search reports
  - [x] `opencti_list_attack_patterns` tool — list MITRE ATT&CK techniques
  - [x] Support stdio and streamable-http transports
  - [x] Graceful error handling for missing API key/URL
- [x] Create `Dockerfile` with python:3.12-slim-bookworm, libmagic1 for pycti
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8370
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8370** — OpenCTI MCP Server (streamable-http)

## Notes

- API-based: uses pycti Python client (not a CLI wrapper)
- Source: https://github.com/OpenCTI-Platform/client-python
- Requires both `OPENCTI_API_KEY` and `OPENCTI_URL` environment variables
- libmagic1 system package required for python-magic (pycti dependency)
- 5 tools for querying indicators, malware, threat actors, reports, and ATT&CK patterns
