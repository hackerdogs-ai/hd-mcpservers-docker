# A2A Scanner MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`a2a-scanner-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping a2a-scanner CLI
  - [x] `run_a2a_scanner` tool — run a2a-scanner with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with a2a-scanner installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8341
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8341** — A2A Scanner MCP Server (streamable-http)

## Notes

- Source: https://github.com/cisco-ai-defense/a2a-scanner
- Binary: `a2a-scanner`
- Install: see https://github.com/cisco-ai-defense/a2a-scanner for installation instructions
