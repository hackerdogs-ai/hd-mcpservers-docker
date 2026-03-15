# theHarvester MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`theharvester-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping theHarvester CLI
  - [x] `run_theharvester` tool — run theHarvester with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Add theHarvester install steps to `Dockerfile` (pip install from [laramies/theHarvester](https://github.com/laramies/theHarvester))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8204
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8204** — theHarvester MCP Server (streamable-http)

## Notes

- Source: https://github.com/laramies/theHarvester
- Binary: `theHarvester`
- Install: see https://github.com/laramies/theHarvester for installation instructions
