# Clair MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`clair-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping clair CLI
  - [x] `run_clair` tool — run clair with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add clair install steps to `Dockerfile` (see [quay/clair](https://github.com/quay/clair))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8270
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8270** — Clair MCP Server (streamable-http)

## Notes

- Source: https://github.com/quay/clair
- Binary: `clair`
- Install: see https://github.com/quay/clair for installation instructions
