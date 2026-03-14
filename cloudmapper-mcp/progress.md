# CloudMapper MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`cloudmapper-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping cloudmapper CLI
  - [x] `run_cloudmapper` tool — run cloudmapper with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Add cloudmapper install steps to `Dockerfile` (see [duo-labs/cloudmapper](https://github.com/duo-labs/cloudmapper))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8268
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8268** — CloudMapper MCP Server (streamable-http)

## Notes

- Source: https://github.com/duo-labs/cloudmapper
- Binary: `cloudmapper`
- Install: see https://github.com/duo-labs/cloudmapper for installation instructions
