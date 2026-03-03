# Hakrawler MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`hakrawler-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping hakrawler CLI
  - [x] `run_hakrawler` tool — run hakrawler with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add hakrawler install steps to `Dockerfile` (see [hakluke/hakrawler](https://github.com/hakluke/hakrawler))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8217
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8217** — Hakrawler MCP Server (streamable-http)

## Notes

- Source: https://github.com/hakluke/hakrawler
- Binary: `hakrawler`
- Install: see https://github.com/hakluke/hakrawler for installation instructions
