# Crunch MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`crunch-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping crunch CLI
  - [x] `run_crunch` tool — run crunch with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with crunch installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8324
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8324** — Crunch MCP Server (streamable-http)

## Notes

- Source: https://github.com/crunchsec/crunch
- Binary: `crunch`
- Install: see https://github.com/crunchsec/crunch for installation instructions
