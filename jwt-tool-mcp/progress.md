# JWT-Tool MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`jwt-tool-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping jwt_tool.py CLI
  - [x] `run_jwt_tool` tool — run jwt_tool.py with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add jwt_tool.py install steps to `Dockerfile` (see [ticarpi/jwt_tool](https://github.com/ticarpi/jwt_tool))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8265
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8265** — JWT-Tool MCP Server (streamable-http)

## Notes

- Source: https://github.com/ticarpi/jwt_tool
- Binary: `jwt_tool.py`
- Install: see https://github.com/ticarpi/jwt_tool for installation instructions
