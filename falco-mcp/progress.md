# Falco MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`falco-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping falco CLI
  - [x] `run_falco` tool — run falco with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add falco install steps to `Dockerfile` (see [falcosecurity/falco](https://github.com/falcosecurity/falco))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8271
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8271** — Falco MCP Server (streamable-http)

## Notes

- Source: https://github.com/falcosecurity/falco
- Binary: `falco`
- Install: see https://github.com/falcosecurity/falco for installation instructions
