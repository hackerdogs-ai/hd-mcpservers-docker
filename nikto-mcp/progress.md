# Nikto MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`nikto-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping nikto CLI
  - [x] `run_nikto` tool — run nikto with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add nikto install steps to `Dockerfile` (see [sullo/nikto](https://github.com/sullo/nikto))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8219
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8219** — Nikto MCP Server (streamable-http)

## Notes

- Source: https://github.com/sullo/nikto
- Binary: `nikto`
- Install: see https://github.com/sullo/nikto for installation instructions
