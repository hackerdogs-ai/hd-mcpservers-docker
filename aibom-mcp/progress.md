# AIBOM MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`aibom-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping aibom CLI
  - [x] `run_aibom` tool — run aibom with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with aibom installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8343
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8343** — AIBOM MCP Server (streamable-http)

## Notes

- Source: https://github.com/cisco-ai-defense/aibom
- Binary: `aibom`
- Install: see https://github.com/cisco-ai-defense/aibom for installation instructions
