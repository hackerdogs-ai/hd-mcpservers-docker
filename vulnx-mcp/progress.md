# Vulnx MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`vulnx-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping vulnx CLI
  - [x] `search_vulnerabilities` tool — search vulnerabilities with filters
  - [x] `get_vulnerability_details` tool — get details for specific CVE(s)
  - [x] `list_search_filters` tool — list available search filter fields
  - [x] `analyze_vulnerabilities` tool — aggregate vulnerabilities by field
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` — multi-stage build (golang:1.23-bookworm builder + python runtime)
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8116
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8116** — Vulnx MCP Server (streamable-http)

## Notes

- Vulnx is the successor to cvemap from ProjectDiscovery
- Source: https://github.com/projectdiscovery/cvemap
- Install: `go install github.com/projectdiscovery/cvemap/cmd/vulnx@latest`
- Subcommands: search, id, filters, analyze, auth, version
- Supports product, vendor, severity, CVSS score filtering

## Code Review Fixes Applied
- [x] Added logging (logging.basicConfig to stdout, logger.info/warning/error)
- [x] Standardized Go version to 1.23 in Dockerfile
- [x] Standardized MCP_TRANSPORT default to stdio
- [x] Fixed JSONL parsing in subprocess output

## Test Suite Improvements
- [x] Rewrote test.sh with standardized MCP client protocol testing
- [x] Tests: Docker image build, CLI binary check, MCP stdio (JSON-RPC init + tools/list), MCP HTTP streamable (init + tools/list + tools/call)
- [x] Proper cleanup with trap, pass/fail counters, colored output
