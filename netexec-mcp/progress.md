# NetExec MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`netexec-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping netexec CLI
  - [x] `run_netexec` tool — run netexec with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add netexec install steps to `Dockerfile` (see [PwnDexter/NetExec](https://github.com/PwnDexter/NetExec))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8212
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8212** — NetExec MCP Server (streamable-http)

## Notes

- Source: https://github.com/PwnDexter/NetExec
- Binary: `netexec`
- Install: see https://github.com/PwnDexter/NetExec for installation instructions
