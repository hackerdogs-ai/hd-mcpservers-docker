# Scout Suite MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`scoutsuite-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping scout CLI
  - [x] `run_scoutsuite` tool — run scout with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add scout install steps to `Dockerfile` (see [nccgroup/ScoutSuite](https://github.com/nccgroup/ScoutSuite))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8251
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8251** — Scout Suite MCP Server (streamable-http)

## Notes

- Source: https://github.com/nccgroup/ScoutSuite
- Binary: `scout`
- Install: see https://github.com/nccgroup/ScoutSuite for installation instructions
