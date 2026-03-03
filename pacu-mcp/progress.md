# Pacu MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`pacu-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping pacu CLI
  - [x] `run_pacu` tool — run pacu with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add pacu install steps to `Dockerfile` (see [RhinoSecurityLabs/pacu](https://github.com/RhinoSecurityLabs/pacu))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8269
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8269** — Pacu MCP Server (streamable-http)

## Notes

- Source: https://github.com/RhinoSecurityLabs/pacu
- Binary: `pacu`
- Install: see https://github.com/RhinoSecurityLabs/pacu for installation instructions
