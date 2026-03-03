# Volatility3 MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`volatility3-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping volatility CLI
  - [x] `run_volatility3` tool — run volatility with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add volatility install steps to `Dockerfile` (see [volatilityfoundation/volatility3](https://github.com/volatilityfoundation/volatility3))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8247
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8247** — Volatility3 MCP Server (streamable-http)

## Notes

- Source: https://github.com/volatilityfoundation/volatility3
- Binary: `volatility`
- Install: see https://github.com/volatilityfoundation/volatility3 for installation instructions
