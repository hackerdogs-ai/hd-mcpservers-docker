# Nova Framework MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`nova-framework-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping nova-framework CLI
  - [x] `run_nova_framework` tool — run nova-framework with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with nova-framework installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8299
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8299** — Nova Framework MCP Server (streamable-http)

## Notes

- Source: https://github.com/Nova-Hunting/nova-framework
- Binary: `nova-framework`
- Install: see https://github.com/Nova-Hunting/nova-framework for installation instructions
