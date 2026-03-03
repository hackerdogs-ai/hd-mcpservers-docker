# NBTScan MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`nbtscan-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping nbtscan CLI
  - [x] `run_nbtscan` tool — run nbtscan with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add nbtscan install steps to `Dockerfile` (see [residuum/nbtscan](https://github.com/residuum/nbtscan))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8206
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8206** — NBTScan MCP Server (streamable-http)

## Notes

- Source: https://github.com/residuum/nbtscan
- Binary: `nbtscan`
- Install: see https://github.com/residuum/nbtscan for installation instructions
