# Pwninit MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`pwninit-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping pwninit CLI
  - [x] `run_pwninit` tool — run pwninit with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add pwninit install steps to `Dockerfile` (see [icecream94/pwninit](https://github.com/icecream94/pwninit))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8278
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8278** — Pwninit MCP Server (streamable-http)

## Notes

- Source: https://github.com/icecream94/pwninit
- Binary: `pwninit`
- Install: see https://github.com/icecream94/pwninit for installation instructions
