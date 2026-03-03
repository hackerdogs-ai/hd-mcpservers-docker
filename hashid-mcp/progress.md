# HashID MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`hashid-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping hashid CLI
  - [x] `run_hashid` tool — run hashid with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add hashid install steps to `Dockerfile` (see [psypanda/hashid](https://github.com/psypanda/hashid))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8264
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8264** — HashID MCP Server (streamable-http)

## Notes

- Source: https://github.com/psypanda/hashid
- Binary: `hashid`
- Install: see https://github.com/psypanda/hashid for installation instructions
