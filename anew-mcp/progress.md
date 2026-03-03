# Anew MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`anew-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping anew CLI
  - [x] `run_anew` tool — run anew with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add anew install steps to `Dockerfile` (see [projectdiscovery/anew](https://github.com/projectdiscovery/anew))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8229
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8229** — Anew MCP Server (streamable-http)

## Notes

- Source: https://github.com/projectdiscovery/anew
- Binary: `anew`
- Install: see https://github.com/projectdiscovery/anew for installation instructions
