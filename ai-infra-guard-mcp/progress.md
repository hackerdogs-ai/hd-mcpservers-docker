# AI-Infra-Guard MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`ai-infra-guard-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping ai-infra-guard CLI
  - [x] `run_ai_infra_guard` tool — run ai-infra-guard with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with ai-infra-guard installation (multi-stage Go build from source)
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8294
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8294** — AI-Infra-Guard MCP Server (streamable-http)

## Notes

- Source: https://github.com/Tencent/AI-Infra-Guard
- Binary: `ai-infra-guard` (Go binary, built from source in multi-stage Docker build)
- The tool has two modes: `scan` (standalone CLI scanner) and `webserver` (web UI on port 8088)
- The MCP server wraps the CLI `scan` subcommand — no backend daemon required
- Data directories (`data/fingerprints`, `data/vuln`, `data/mcp`) are included in the image
- v4.0 includes 47 fingerprints and 589 vulnerability rules across 40+ AI components
