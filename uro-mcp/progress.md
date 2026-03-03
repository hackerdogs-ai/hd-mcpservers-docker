# Uro MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`uro-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping uro CLI
  - [x] `run_uro` tool — run uro with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add uro install steps to `Dockerfile` (see [projectdiscovery/uro](https://github.com/projectdiscovery/uro))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8228
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8228** — Uro MCP Server (streamable-http)

## Notes

- Source: https://github.com/projectdiscovery/uro
- Binary: `uro`
- Install: see https://github.com/projectdiscovery/uro for installation instructions
