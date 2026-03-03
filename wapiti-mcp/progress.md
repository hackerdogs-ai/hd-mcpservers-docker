# Wapiti MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`wapiti-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping wapiti CLI
  - [x] `run_wapiti` tool — run wapiti with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with wapiti installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8288
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8288** — Wapiti MCP Server (streamable-http)

## Notes

- Source: https://github.com/wapiti-scanner/wapiti
- Binary: `wapiti`
- Install: see https://github.com/wapiti-scanner/wapiti for installation instructions
