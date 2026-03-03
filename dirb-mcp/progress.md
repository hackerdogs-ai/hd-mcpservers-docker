# Dirb MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`dirb-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping dirb CLI
  - [x] `run_dirb` tool — run dirb with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add dirb install steps to `Dockerfile` (see [darkoperator/dirb](https://github.com/darkoperator/dirb))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8214
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8214** — Dirb MCP Server (streamable-http)

## Notes

- Source: https://github.com/darkoperator/dirb
- Binary: `dirb`
- Install: see https://github.com/darkoperator/dirb for installation instructions
