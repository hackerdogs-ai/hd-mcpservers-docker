# TestDisk MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`testdisk-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping testdisk CLI
  - [x] `run_testdisk` tool — run testdisk with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add testdisk install steps to `Dockerfile` (see [cgsecurity/testdisk](https://github.com/cgsecurity/testdisk))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8283
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8283** — TestDisk MCP Server (streamable-http)

## Notes

- Source: https://github.com/cgsecurity/testdisk
- Binary: `testdisk`
- Install: see https://github.com/cgsecurity/testdisk for installation instructions
