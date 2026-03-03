# Subjack MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`subjack-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping subjack CLI
  - [x] `run_subjack` tool — run subjack with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add subjack install steps to `Dockerfile` (see [haccer/subjack](https://github.com/haccer/subjack))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8260
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8260** — Subjack MCP Server (streamable-http)

## Notes

- Source: https://github.com/haccer/subjack
- Binary: `subjack`
- Install: see https://github.com/haccer/subjack for installation instructions
