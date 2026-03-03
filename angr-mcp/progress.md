# Angr MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`angr-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping python3 CLI
  - [x] `run_angr` tool — run python3 with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add python3 install steps to `Dockerfile` (see [angr/angr](https://github.com/angr/angr))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8246
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8246** — Angr MCP Server (streamable-http)

## Notes

- Source: https://github.com/angr/angr
- Binary: `python3`
- Install: see https://github.com/angr/angr for installation instructions
