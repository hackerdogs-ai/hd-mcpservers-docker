# Foremost MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`foremost-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping foremost CLI
  - [x] `run_foremost` tool — run foremost with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add foremost install steps to `Dockerfile` (see [kdz/foremost](https://github.com/kdz/foremost))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8249
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8249** — Foremost MCP Server (streamable-http)

## Notes

- Source: https://github.com/kdz/foremost
- Binary: `foremost`
- Install: see https://github.com/kdz/foremost for installation instructions
