# Yeti MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`yeti-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping yeti-mcp CLI
  - [x] `run_yeti_mcp` tool — run yeti-mcp with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with yeti-mcp installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8337
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8337** — Yeti MCP Server (streamable-http)

## Notes

- Source: https://github.com/yeti-platform/yeti-mcp
- Binary: `yeti-mcp`
- Install: see https://github.com/yeti-platform/yeti-mcp for installation instructions
