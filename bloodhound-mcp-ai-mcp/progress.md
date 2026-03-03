# BloodHound AI MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`bloodhound-mcp-ai-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping bloodhound-mcp CLI
  - [x] `run_bloodhound_mcp` tool — run bloodhound-mcp with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with bloodhound-mcp installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8338
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8338** — BloodHound AI MCP Server (streamable-http)

## Notes

- Source: https://github.com/stevenyu113228/BloodHound-MCP
- Binary: `bloodhound-mcp`
- Install: see https://github.com/stevenyu113228/BloodHound-MCP for installation instructions
