# Checkov MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`checkov-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping checkov CLI
  - [x] `run_checkov` tool — run checkov with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add checkov install steps to `Dockerfile` (see [bridgecrewio/checkov](https://github.com/bridgecrewio/checkov))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8272
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8272** — Checkov MCP Server (streamable-http)

## Notes

- Source: https://github.com/bridgecrewio/checkov
- Binary: `checkov`
- Install: see https://github.com/bridgecrewio/checkov for installation instructions
