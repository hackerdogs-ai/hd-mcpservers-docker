# Trivy Neutr0n MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`trivy-neutr0n-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping trivy-mcp CLI
  - [x] `run_trivy_mcp` tool — run trivy-mcp with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with trivy-mcp installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8356
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8356** — Trivy Neutr0n MCP Server (streamable-http)

## Notes

- Source: https://github.com/Mr-Neutr0n/trivy-mcp-server
- Binary: `trivy-mcp`
- Install: see https://github.com/Mr-Neutr0n/trivy-mcp-server for installation instructions
