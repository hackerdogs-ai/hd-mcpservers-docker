# CORScanner MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`corscanner-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping cors_scan CLI
  - [x] `run_cors_scan` tool — run cors_scan with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with cors_scan installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8292
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8292** — CORScanner MCP Server (streamable-http)

## Notes

- Source: https://github.com/chenjj/CORScanner
- Binary: `cors_scan`
- Install: see https://github.com/chenjj/CORScanner for installation instructions
