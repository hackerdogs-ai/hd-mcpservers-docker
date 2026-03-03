# Hydra MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`hydra-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping hydra CLI
  - [x] `run_hydra` tool — run hydra with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add hydra install steps to `Dockerfile` (see [vanhauser-thc/thc-hydra](https://github.com/vanhauser-thc/thc-hydra))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8233
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8233** — Hydra MCP Server (streamable-http)

## Notes

- Source: https://github.com/vanhauser-thc/thc-hydra
- Binary: `hydra`
- Install: see https://github.com/vanhauser-thc/thc-hydra for installation instructions
