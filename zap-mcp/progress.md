# OWASP ZAP MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`zap-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping zap.sh CLI
  - [x] `run_zap` tool — run zap.sh with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add zap.sh install steps to `Dockerfile` (see [zaproxy/zap-core](https://github.com/zaproxy/zap-core))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8231
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8231** — OWASP ZAP MCP Server (streamable-http)

## Notes

- Source: https://github.com/zaproxy/zap-core
- Binary: `zap.sh`
- Install: see https://github.com/zaproxy/zap-core for installation instructions
