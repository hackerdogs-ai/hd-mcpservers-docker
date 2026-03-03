# GAU MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`gau-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping gau CLI
  - [x] `run_gau` tool — run gau with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add gau install steps to `Dockerfile` (see [lc/gau](https://github.com/lc/gau))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8218
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8218** — GAU MCP Server (streamable-http)

## Notes

- Source: https://github.com/lc/gau
- Binary: `gau`
- Install: see https://github.com/lc/gau for installation instructions
