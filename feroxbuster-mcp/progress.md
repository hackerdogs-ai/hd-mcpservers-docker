# Feroxbuster MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`feroxbuster-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping feroxbuster CLI
  - [x] `run_feroxbuster` tool — run feroxbuster with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add feroxbuster install steps to `Dockerfile` (see [epi052/feroxbuster](https://github.com/epi052/feroxbuster))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8216
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8216** — Feroxbuster MCP Server (streamable-http)

## Notes

- Source: https://github.com/epi052/feroxbuster
- Binary: `feroxbuster`
- Install: see https://github.com/epi052/feroxbuster for installation instructions
