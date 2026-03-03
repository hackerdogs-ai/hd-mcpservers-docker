# Capa MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`capa-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping capa CLI
  - [x] `run_capa` tool — run capa with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with capa installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8329
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8329** — Capa MCP Server (streamable-http)

## Notes

- Source: https://github.com/mandiant/capa
- Binary: `capa`
- Install: see https://github.com/mandiant/capa for installation instructions
