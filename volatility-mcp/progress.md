# Volatility MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`volatility-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping vol.py CLI
  - [x] `run_volatility` tool — run vol.py with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add vol.py install steps to `Dockerfile` (see [volatilityfoundation/volatility](https://github.com/volatilityfoundation/volatility))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8248
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8248** — Volatility MCP Server (streamable-http)

## Notes

- Source: https://github.com/volatilityfoundation/volatility
- Binary: `vol.py`
- Install: see https://github.com/volatilityfoundation/volatility for installation instructions
