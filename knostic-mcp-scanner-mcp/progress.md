# Knostic Scanner MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`knostic-mcp-scanner-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping mcp-scanner CLI
  - [x] `run_mcp_scanner` tool — run mcp-scanner with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with mcp-scanner installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8344
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8344** — Knostic Scanner MCP Server (streamable-http)

## Notes

- Source: https://github.com/knostic/MCP-Scanner
- Binary: `mcp-scanner`
- Install: see https://github.com/knostic/MCP-Scanner for installation instructions
