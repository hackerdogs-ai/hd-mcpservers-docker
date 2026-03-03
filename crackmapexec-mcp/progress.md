# CrackMapExec MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`crackmapexec-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping crackmapexec CLI
  - [x] `run_crackmapexec` tool — run crackmapexec with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add crackmapexec install steps to `Dockerfile` (see [byt3bl33d3r/CrackMapExec](https://github.com/byt3bl33d3r/CrackMapExec))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8208
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8208** — CrackMapExec MCP Server (streamable-http)

## Notes

- Source: https://github.com/byt3bl33d3r/CrackMapExec
- Binary: `crackmapexec`
- Install: see https://github.com/byt3bl33d3r/CrackMapExec for installation instructions
