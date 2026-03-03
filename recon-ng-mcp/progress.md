# Recon-ng MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`recon-ng-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping recon-ng CLI
  - [x] `run_recon_ng` tool — run recon-ng with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add recon-ng install steps to `Dockerfile` (see [lanmaster53/recon-ng](https://github.com/lanmaster53/recon-ng))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8256
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8256** — Recon-ng MCP Server (streamable-http)

## Notes

- Source: https://github.com/lanmaster53/recon-ng
- Binary: `recon-ng`
- Install: see https://github.com/lanmaster53/recon-ng for installation instructions
