# ROPgadget MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`ropgadget-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping ROPgadget CLI
  - [x] `run_ropgadget` tool — run ROPgadget with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add ROPgadget install steps to `Dockerfile` (see [JonathanSalwan/ROPgadget](https://github.com/JonathanSalwan/ROPgadget))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8242
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8242** — ROPgadget MCP Server (streamable-http)

## Notes

- Source: https://github.com/JonathanSalwan/ROPgadget
- Binary: `ROPgadget`
- Install: see https://github.com/JonathanSalwan/ROPgadget for installation instructions
