# Binwalk MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`binwalk-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping binwalk CLI
  - [x] `run_binwalk` tool — run binwalk with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add binwalk install steps to `Dockerfile` (see [ReFirmLabs/binwalk](https://github.com/ReFirmLabs/binwalk))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8241
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8241** — Binwalk MCP Server (streamable-http)

## Notes

- Source: https://github.com/ReFirmLabs/binwalk
- Binary: `binwalk`
- Install: see https://github.com/ReFirmLabs/binwalk for installation instructions
