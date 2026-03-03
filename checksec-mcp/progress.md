# Checksec MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`checksec-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping checksec CLI
  - [x] `run_checksec` tool — run checksec with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add checksec install steps to `Dockerfile` (see [slimm609/checksec.sh](https://github.com/slimm609/checksec.sh))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8244
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8244** — Checksec MCP Server (streamable-http)

## Notes

- Source: https://github.com/slimm609/checksec.sh
- Binary: `checksec`
- Install: see https://github.com/slimm609/checksec.sh for installation instructions
