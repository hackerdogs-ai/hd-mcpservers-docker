# John the Ripper MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`john-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping john CLI
  - [x] `run_john` tool — run john with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add john install steps to `Dockerfile` (see [openwall/john](https://github.com/openwall/john))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8234
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8234** — John the Ripper MCP Server (streamable-http)

## Notes

- Source: https://github.com/openwall/john
- Binary: `john`
- Install: see https://github.com/openwall/john for installation instructions
