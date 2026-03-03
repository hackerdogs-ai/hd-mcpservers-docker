# Patator MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`patator-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping patator CLI
  - [x] `run_patator` tool — run patator with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add patator install steps to `Dockerfile` (see [lanjelot/patator](https://github.com/lanjelot/patator))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8262
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8262** — Patator MCP Server (streamable-http)

## Notes

- Source: https://github.com/lanjelot/patator
- Binary: `patator`
- Install: see https://github.com/lanjelot/patator for installation instructions
