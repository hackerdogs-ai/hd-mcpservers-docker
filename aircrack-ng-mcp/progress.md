# Aircrack-ng MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`aircrack-ng-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping aircrack-ng CLI
  - [x] `run_aircrack_ng` tool — run aircrack-ng with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with aircrack-ng installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8321
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8321** — Aircrack-ng MCP Server (streamable-http)

## Notes

- Source: https://github.com/aircrack-ng/aircrack-ng
- Binary: `aircrack-ng`
- Install: see https://github.com/aircrack-ng/aircrack-ng for installation instructions
