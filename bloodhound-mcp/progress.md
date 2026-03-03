# BloodHound MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`bloodhound-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping bloodhound-python CLI
  - [x] `run_bloodhound_python` tool — run bloodhound-python with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with bloodhound-python installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8286
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8286** — BloodHound MCP Server (streamable-http)

## Notes

- Source: https://github.com/SpecterOps/BloodHound
- Binary: `bloodhound-python`
- Install: see https://github.com/SpecterOps/BloodHound for installation instructions
