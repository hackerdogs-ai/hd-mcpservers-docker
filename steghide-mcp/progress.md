# Steghide MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`steghide-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping steghide CLI
  - [x] `run_steghide` tool — run steghide with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add steghide install steps to `Dockerfile` (see [StefanHetze/steghide](https://github.com/StefanHetze/steghide))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8250
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8250** — Steghide MCP Server (streamable-http)

## Notes

- Source: https://github.com/StefanHetze/steghide
- Binary: `steghide`
- Install: see https://github.com/StefanHetze/steghide for installation instructions
