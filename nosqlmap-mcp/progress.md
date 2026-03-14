# NoSQLMap MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`nosqlmap-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping nosqlmap CLI
  - [x] `run_nosqlmap` tool — run nosqlmap with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Add nosqlmap install steps to `Dockerfile` (see [codingo/NoSQLMap](https://github.com/codingo/NoSQLMap))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8266
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8266** — NoSQLMap MCP Server (streamable-http)

## Notes

- Source: https://github.com/codingo/NoSQLMap
- Binary: `nosqlmap`
- Install: see https://github.com/codingo/NoSQLMap for installation instructions
