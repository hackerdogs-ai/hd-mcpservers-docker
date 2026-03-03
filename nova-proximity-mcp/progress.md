# Nova Proximity MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`nova-proximity-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping nova-proximity CLI
  - [x] `run_nova_proximity` tool — run nova-proximity with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with nova-proximity installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8298
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8298** — Nova Proximity MCP Server (streamable-http)

## Notes

- Source: https://github.com/Nova-Hunting/nova-proximity
- Binary: `nova-proximity`
- Install: see https://github.com/Nova-Hunting/nova-proximity for installation instructions
