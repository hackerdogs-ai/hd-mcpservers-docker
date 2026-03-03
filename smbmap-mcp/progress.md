# SMBMap MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`smbmap-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping smbmap CLI
  - [x] `run_smbmap` tool — run smbmap with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add smbmap install steps to `Dockerfile` (see [ShaunBarton/smbmap](https://github.com/ShaunBarton/smbmap))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8211
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8211** — SMBMap MCP Server (streamable-http)

## Notes

- Source: https://github.com/ShaunBarton/smbmap
- Binary: `smbmap`
- Install: see https://github.com/ShaunBarton/smbmap for installation instructions
