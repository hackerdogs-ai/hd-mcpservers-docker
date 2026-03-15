# Subfinder MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`subfinder-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping subfinder CLI
  - [x] `enumerate_subdomains` tool — structured subdomain discovery with filtering
  - [x] `run_subfinder` tool — raw CLI passthrough for advanced usage
  - [x] `list_subfinder_sources` tool — list available enumeration sources
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with multi-stage build (Go builder for subfinder binary)
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8367
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8367** — Subfinder MCP Server (streamable-http)

## Notes

- Source: https://github.com/projectdiscovery/subfinder
- Binary: `subfinder`
- Install: multi-stage Docker build using `go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest`
- Reference implementation (Go): https://github.com/copyleftdev/mcp_subfinder_server
