# GHunt MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`ghunt-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping ghunt CLI
  - [x] `run_ghunt` tool — run ghunt with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Add ghunt install steps to `Dockerfile`
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8218
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable
- [x] Build and test Docker image (6/6 tests pass)

## Port Assignment

- **8218** — GHunt MCP Server (streamable-http)

## Notes

- Source: https://github.com/mxrch/GHunt
- Binary: `ghunt`
- GHunt may require Google authentication/cookies for full functionality. Basic lookups work without keys.
