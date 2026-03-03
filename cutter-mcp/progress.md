# Cutter MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`cutter-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping cutter CLI
  - [x] `run_cutter` tool — run cutter with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with cutter installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8320
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8320** — Cutter MCP Server (streamable-http)

## Notes

- Source: https://github.com/rizinorg/cutter
- Binary: `cutter`
- Install: see https://github.com/rizinorg/cutter for installation instructions
