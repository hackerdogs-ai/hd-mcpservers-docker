# Terrascan MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`terrascan-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping terrascan CLI
  - [x] `run_terrascan` tool — run terrascan with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add terrascan install steps to `Dockerfile` (see [tenable/terrascan](https://github.com/tenable/terrascan))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8273
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8273** — Terrascan MCP Server (streamable-http)

## Notes

- Source: https://github.com/tenable/terrascan
- Binary: `terrascan`
- Install: see https://github.com/tenable/terrascan for installation instructions
