# Ghidra MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`ghidra-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping analyzeHeadless CLI
  - [x] `run_ghidra` tool — run analyzeHeadless with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add analyzeHeadless install steps to `Dockerfile` (see [NationalSecurityAgency/ghidra](https://github.com/NationalSecurityAgency/ghidra))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8240
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8240** — Ghidra MCP Server (streamable-http)

## Notes

- Source: https://github.com/NationalSecurityAgency/ghidra
- Binary: `analyzeHeadless`
- Install: see https://github.com/NationalSecurityAgency/ghidra for installation instructions
