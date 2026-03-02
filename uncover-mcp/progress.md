# Uncover MCP Server - Progress

## Setup Steps

- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping uncover CLI
  - [x] `search_hosts` tool — search for exposed hosts via search APIs
  - [x] Support `MCP_TRANSPORT` and `MCP_PORT` (8107)
  - [x] Support stdio and streamable-http transports
- [x] Create `Dockerfile` with multi-stage golang build for uncover
- [x] Create `publish_to_hackerdogs.sh` with `IMAGE_NAME="uncover-mcp"`
- [x] Create `mcpServer.json` with docker pattern
- [x] Create `docker-compose.yml` with port 8107
- [x] Create `test.sh` for MCP server testing
- [x] Create `README.md` with Hackerdogs logo and documentation
- [x] Create `progress.md` to track progress

## Code Review Fixes Applied
- [x] Added logging (logging.basicConfig to stdout, logger.info/warning/error)
- [x] Standardized Go version to 1.23 in Dockerfile
- [x] Standardized MCP_TRANSPORT default to stdio
- [x] Fixed JSONL parsing in subprocess output

## Test Suite Improvements
- [x] Rewrote test.sh with standardized MCP client protocol testing
- [x] Tests: Docker image build, CLI binary check, MCP stdio (JSON-RPC init + tools/list), MCP HTTP streamable (init + tools/list + tools/call)
- [x] Proper cleanup with trap, pass/fail counters, colored output
