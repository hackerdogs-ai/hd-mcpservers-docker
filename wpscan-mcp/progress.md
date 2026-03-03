# WPScan MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`wpscan-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping wpscan CLI
  - [x] `run_wpscan` tool — run wpscan with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add wpscan install steps to `Dockerfile` (see [wpscanteam/wpscan](https://github.com/wpscanteam/wpscan))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8220
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8220** — WPScan MCP Server (streamable-http)

## Notes

- Source: https://github.com/wpscanteam/wpscan
- Binary: `wpscan`
- Install: see https://github.com/wpscanteam/wpscan for installation instructions
