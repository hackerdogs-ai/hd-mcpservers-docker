# Cvemap MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`cvemap-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping cvemap CLI
  - [x] `search_cves` tool — search CVEs with filters
  - [x] `get_cve_details` tool — get details for specific CVE(s)
  - [x] `list_filters` tool — list available search filter fields
  - [x] `analyze_cves` tool — aggregate CVEs by field
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` — multi-stage build (golang:1.23-bookworm builder + python runtime)
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8106
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8106** — Cvemap MCP Server (streamable-http)

## Notes

- Cvemap source: https://github.com/projectdiscovery/cvemap
- Install: `go install github.com/projectdiscovery/cvemap/cmd/cvemap@latest`
- Search, filter, and analyze CVE/vulnerability data
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
