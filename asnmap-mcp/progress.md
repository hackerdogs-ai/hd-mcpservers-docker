# Asnmap MCP Server - Progress

## Setup Steps

- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping asnmap CLI
  - [x] `lookup_asn` tool — look up network ranges by ASN
  - [x] `lookup_ip` tool — look up ASN info for IP
  - [x] `lookup_domain` tool — look up ASN info for domain
  - [x] `lookup_org` tool — look up ASN info for organization
  - [x] Support `MCP_TRANSPORT` and `MCP_PORT` (8110)
  - [x] Support stdio and streamable-http transports
- [x] Create `Dockerfile` with multi-stage golang build for asnmap
- [x] Create `publish_to_hackerdogs.sh` with `IMAGE_NAME="asnmap-mcp"`
- [x] Create `mcpServer.json` with docker pattern
- [x] Create `docker-compose.yml` with port 8110
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
