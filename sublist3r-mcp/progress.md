# Sublist3r MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`sublist3r-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping sublist3r CLI
  - [x] `run_sublist3r` tool — run sublist3r with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with sublist3r installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8301
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8301** — Sublist3r MCP Server (streamable-http)

## Notes

- Source: https://github.com/aboul3la/Sublist3r
- Binary: `sublist3r`
- Install: see https://github.com/aboul3la/Sublist3r for installation instructions
