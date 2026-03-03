# Dalfox MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`dalfox-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping dalfox CLI
  - [x] `run_dalfox` tool — run dalfox with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add dalfox install steps to `Dockerfile` (see [hahwul/dalfox](https://github.com/hahwul/dalfox))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8221
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8221** — Dalfox MCP Server (streamable-http)

## Notes

- Source: https://github.com/hahwul/dalfox
- Binary: `dalfox`
- Install: see https://github.com/hahwul/dalfox for installation instructions
