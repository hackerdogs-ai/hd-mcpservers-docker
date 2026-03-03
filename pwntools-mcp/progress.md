# Pwntools MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`pwntools-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping python3 CLI
  - [x] `run_pwntools` tool — run python3 with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add python3 install steps to `Dockerfile` (see [Gallopsled/pwntools](https://github.com/Gallopsled/pwntools))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8245
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8245** — Pwntools MCP Server (streamable-http)

## Notes

- Source: https://github.com/Gallopsled/pwntools
- Binary: `python3`
- Install: see https://github.com/Gallopsled/pwntools for installation instructions
