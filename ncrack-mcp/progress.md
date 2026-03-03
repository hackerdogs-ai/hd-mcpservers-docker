# Ncrack MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`ncrack-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping ncrack CLI
  - [x] `run_ncrack` tool — run ncrack with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with ncrack installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8306
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8306** — Ncrack MCP Server (streamable-http)

## Notes

- Source: https://github.com/nmap/ncrack
- Binary: `ncrack`
- Install: see https://github.com/nmap/ncrack for installation instructions
