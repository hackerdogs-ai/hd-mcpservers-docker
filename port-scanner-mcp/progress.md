# Port Scanner MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`port-scanner-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping port-scanner CLI
  - [x] `run_port_scanner` tool — run port-scanner with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with port-scanner installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8354
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8354** — Port Scanner MCP Server (streamable-http)

## Notes

- Source: https://github.com/relaxcloud-cn/mcp-port-scanner
- Binary: `port-scanner`
- Install: see https://github.com/relaxcloud-cn/mcp-port-scanner for installation instructions
