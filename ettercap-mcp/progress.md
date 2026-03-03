# Ettercap MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`ettercap-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping ettercap CLI
  - [x] `run_ettercap` tool — run ettercap with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with ettercap installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8313
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8313** — Ettercap MCP Server (streamable-http)

## Notes

- Source: https://github.com/Ettercap/ettercap
- Binary: `ettercap`
- Install: see https://github.com/Ettercap/ettercap for installation instructions
