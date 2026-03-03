# Radare2 MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`radare2-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping r2 CLI
  - [x] `run_radare2` tool — run r2 with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add r2 install steps to `Dockerfile` (see [radareorg/radare2](https://github.com/radareorg/radare2))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8239
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8239** — Radare2 MCP Server (streamable-http)

## Notes

- Source: https://github.com/radareorg/radare2
- Binary: `r2`
- Install: see https://github.com/radareorg/radare2 for installation instructions
