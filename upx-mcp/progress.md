# UPX MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`upx-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping upx CLI
  - [x] `run_upx` tool — run upx with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add upx install steps to `Dockerfile` (see [upx/upx](https://github.com/upx/upx))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8284
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8284** — UPX MCP Server (streamable-http)

## Notes

- Source: https://github.com/upx/upx
- Binary: `upx`
- Install: see https://github.com/upx/upx for installation instructions
