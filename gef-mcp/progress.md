# GDB-GEF MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`gef-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping gdb CLI
  - [x] `run_gef` tool — run gdb with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add gdb install steps to `Dockerfile` (see [hugsy/gef](https://github.com/hugsy/gef))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8238
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8238** — GDB-GEF MCP Server (streamable-http)

## Notes

- Source: https://github.com/hugsy/gef
- Binary: `gdb`
- Install: see https://github.com/hugsy/gef for installation instructions
