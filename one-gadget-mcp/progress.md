# One-Gadget MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`one-gadget-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping one_gadget CLI
  - [x] `run_one_gadget` tool — run one_gadget with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add one_gadget install steps to `Dockerfile` (see [david942j/one_gadget](https://github.com/david942j/one_gadget))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8276
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8276** — One-Gadget MCP Server (streamable-http)

## Notes

- Source: https://github.com/david942j/one_gadget
- Binary: `one_gadget`
- Install: see https://github.com/david942j/one_gadget for installation instructions
