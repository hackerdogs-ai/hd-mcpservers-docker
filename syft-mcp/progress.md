# Syft MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`syft-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping syft CLI
  - [x] `run_syft` tool — run syft with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with syft installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8358
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8358** — Syft MCP Server (streamable-http)

## Notes

- Source: https://github.com/anchore/syft
- Binary: `syft`
- Install: see https://github.com/anchore/syft for installation instructions
