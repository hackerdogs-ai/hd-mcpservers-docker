# Horusec MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`horusec-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping horusec CLI
  - [x] `run_horusec` tool — run horusec with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with horusec installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8359
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8359** — Horusec MCP Server (streamable-http)

## Notes

- Source: https://github.com/Checkmarx/Horusec
- Binary: `horusec`
- Install: see https://github.com/Checkmarx/Horusec for installation instructions
