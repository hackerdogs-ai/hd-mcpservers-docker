# SMTP User Enum MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`smtp-user-enum-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping smtp-user-enum CLI
  - [x] `run_smtp_user_enum` tool — run smtp-user-enum with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with smtp-user-enum installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8325
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8325** — SMTP User Enum MCP Server (streamable-http)

## Notes

- Source: https://github.com/pentestmonkey/smtp-user-enum
- Binary: `smtp-user-enum`
- Install: see https://github.com/pentestmonkey/smtp-user-enum for installation instructions
