# Ngrep MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`ngrep-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping ngrep CLI
  - [x] `run_ngrep` tool — run ngrep with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with ngrep installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8314
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8314** — Ngrep MCP Server (streamable-http)

## Notes

- Source: https://github.com/jpr5/ngrep
- Binary: `ngrep`
- Install: see https://github.com/jpr5/ngrep for installation instructions
