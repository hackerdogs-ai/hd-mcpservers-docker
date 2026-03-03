# Tplmap MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`tplmap-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping tplmap CLI
  - [x] `run_tplmap` tool — run tplmap with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add tplmap install steps to `Dockerfile` (see [epinna/tplmap](https://github.com/epinna/tplmap))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8267
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8267** — Tplmap MCP Server (streamable-http)

## Notes

- Source: https://github.com/epinna/tplmap
- Binary: `tplmap`
- Install: see https://github.com/epinna/tplmap for installation instructions
