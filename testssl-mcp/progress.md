# TestSSL MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`testssl-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping testssl.sh CLI
  - [x] `run_testssl` tool — run testssl.sh with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add testssl.sh install steps to `Dockerfile` (see [drwetter/testssl.sh](https://github.com/drwetter/testssl.sh))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8279
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8279** — TestSSL MCP Server (streamable-http)

## Notes

- Source: https://github.com/drwetter/testssl.sh
- Binary: `testssl.sh`
- Install: see https://github.com/drwetter/testssl.sh for installation instructions
