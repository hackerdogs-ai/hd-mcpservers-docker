# Gobuster MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`gobuster-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping gobuster CLI
  - [x] `run_gobuster` tool — run gobuster with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add gobuster install steps to `Dockerfile` (see [OWASP/gobuster](https://github.com/OWASP/gobuster))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8213
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8213** — Gobuster MCP Server (streamable-http)

## Notes

- Source: https://github.com/OWASP/gobuster
- Binary: `gobuster`
- Install: see https://github.com/OWASP/gobuster for installation instructions
