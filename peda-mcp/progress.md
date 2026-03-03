# GDB-PEDA MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`peda-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping gdb CLI
  - [x] `run_peda` tool — run gdb with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add gdb install steps to `Dockerfile` (see [longld/peda](https://github.com/longld/peda))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8237
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8237** — GDB-PEDA MCP Server (streamable-http)

## Notes

- Source: https://github.com/longld/peda
- Binary: `gdb`
- Install: see https://github.com/longld/peda for installation instructions
