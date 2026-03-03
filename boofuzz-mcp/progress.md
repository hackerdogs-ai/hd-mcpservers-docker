# Boofuzz MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`boofuzz-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping boofuzz CLI
  - [x] `run_boofuzz` tool — run boofuzz with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with boofuzz installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8333
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8333** — Boofuzz MCP Server (streamable-http)

## Notes

- Source: https://github.com/jtpereyda/boofuzz
- Binary: `boofuzz`
- Install: see https://github.com/jtpereyda/boofuzz for installation instructions
