# DotDotPwn MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`dotdotpwn-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping dotdotpwn CLI
  - [x] `run_dotdotpwn` tool — run dotdotpwn with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add dotdotpwn install steps to `Dockerfile` (see [wireghoul/dotdotpwn](https://github.com/wireghoul/dotdotpwn))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8223
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8223** — DotDotPwn MCP Server (streamable-http)

## Notes

- Source: https://github.com/wireghoul/dotdotpwn
- Binary: `dotdotpwn`
- Install: see https://github.com/wireghoul/dotdotpwn for installation instructions
