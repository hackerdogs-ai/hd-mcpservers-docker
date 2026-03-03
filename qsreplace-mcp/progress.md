# QSReplace MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`qsreplace-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping qsreplace CLI
  - [x] `run_qsreplace` tool — run qsreplace with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add qsreplace install steps to `Dockerfile` (see [projectdiscovery/qsreplace](https://github.com/projectdiscovery/qsreplace))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8227
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8227** — QSReplace MCP Server (streamable-http)

## Notes

- Source: https://github.com/projectdiscovery/qsreplace
- Binary: `qsreplace`
- Install: see https://github.com/projectdiscovery/qsreplace for installation instructions
