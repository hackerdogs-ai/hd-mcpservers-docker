# Hashcat MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`hashcat-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping hashcat CLI
  - [x] `run_hashcat` tool — run hashcat with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add hashcat install steps to `Dockerfile` (see [hashcat/hashcat](https://github.com/hashcat/hashcat))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8235
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8235** — Hashcat MCP Server (streamable-http)

## Notes

- Source: https://github.com/hashcat/hashcat
- Binary: `hashcat`
- Install: see https://github.com/hashcat/hashcat for installation instructions
