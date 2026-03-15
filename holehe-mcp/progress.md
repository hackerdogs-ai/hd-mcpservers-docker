# Holehe MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`holehe-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping holehe CLI
  - [x] `run_holehe` tool — run holehe with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Add holehe install steps to `Dockerfile`
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8219
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable
- [x] Build and test Docker image (6/6 tests pass)

## Port Assignment

- **8219** — Holehe MCP Server (streamable-http)

## Notes

- Source: pip install holehe
- Binary: `holehe`
- Checks email registration across 120+ websites including social media, shopping, dating, and more.
