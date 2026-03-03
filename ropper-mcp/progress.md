# Ropper MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`ropper-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping ropper CLI
  - [x] `run_ropper` tool — run ropper with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add ropper install steps to `Dockerfile` (see [sashs/Ropper](https://github.com/sashs/Ropper))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8243
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8243** — Ropper MCP Server (streamable-http)

## Notes

- Source: https://github.com/sashs/Ropper
- Binary: `ropper`
- Install: see https://github.com/sashs/Ropper for installation instructions
