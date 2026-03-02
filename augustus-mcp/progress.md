# Augustus MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`augustus-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping augustus CLI
  - [x] `scan_llm` tool — run adversarial vulnerability scans
  - [x] `list_components` tool — list probes/detectors/generators/harnesses/buffs
  - [x] `get_version` tool — show version info
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
- [x] Create `Dockerfile` — multi-stage build (golang:1.23-bookworm builder + python runtime)
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8101
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8101** — Augustus MCP Server (streamable-http)

## Notes

- Augustus source: https://github.com/praetorian-inc/augustus
- Install: `go install github.com/praetorian-inc/augustus/cmd/augustus@latest`
- 210+ probes, 28 LLM providers
- Tests: prompt injection, jailbreaks, encoding exploits, data extraction

## Code Review Fixes Applied
- [x] Added logging (logging.basicConfig to stdout, logger.info/warning/error)
- [x] Standardized Go version to 1.23 in Dockerfile
- [x] Standardized MCP_TRANSPORT default to stdio
- [x] Fixed JSONL parsing in subprocess output

## Test Suite Improvements
- [x] Rewrote test.sh with standardized MCP client protocol testing
- [x] Tests: Docker image build, CLI binary check, MCP stdio (JSON-RPC init + tools/list), MCP HTTP streamable (init + tools/list + tools/call)
- [x] Proper cleanup with trap, pass/fail counters, colored output
