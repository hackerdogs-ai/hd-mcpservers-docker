# AI-Infra-Guard MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`ai-infra-guard-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping ai-infra-guard CLI
  - [x] `run_ai_infra_guard` tool — run ai-infra-guard with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with ai-infra-guard installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8294
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8294** — AI-Infra-Guard MCP Server (streamable-http)

## Notes

- Source: https://github.com/Tencent/AI-Infra-Guard
- Binary: `ai-infra-guard`
- Install: see https://github.com/Tencent/AI-Infra-Guard for installation instructions
