# Enum4linux-ng MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`enum4linux-ng-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping enum4linux-ng CLI
  - [x] `run_enum4linux_ng` tool — run enum4linux-ng with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add enum4linux-ng install steps to `Dockerfile` (see [cddc/enum4linux-ng](https://github.com/cddc/enum4linux-ng))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8210
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8210** — Enum4linux-ng MCP Server (streamable-http)

## Notes

- Source: https://github.com/cddc/enum4linux-ng
- Binary: `enum4linux-ng`
- Install: see https://github.com/cddc/enum4linux-ng for installation instructions
