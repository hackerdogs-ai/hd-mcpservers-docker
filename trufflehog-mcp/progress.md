# TruffleHog MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`trufflehog-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping trufflehog CLI
  - [x] `run_trufflehog` tool — run trufflehog with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add trufflehog install steps to `Dockerfile` (see [trufflesecurity/trufflehog](https://github.com/trufflesecurity/trufflehog))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8258
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8258** — TruffleHog MCP Server (streamable-http)

## Notes

- Source: https://github.com/trufflesecurity/trufflehog
- Binary: `trufflehog`
- Install: see https://github.com/trufflesecurity/trufflehog for installation instructions
