# Semgrep MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`semgrep-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping semgrep CLI
  - [x] `run_semgrep` tool — run semgrep with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with semgrep installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8335
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8335** — Semgrep MCP Server (streamable-http)

## Notes

- Source: https://github.com/semgrep/semgrep
- Binary: `semgrep`
- Install: see https://github.com/semgrep/semgrep for installation instructions
