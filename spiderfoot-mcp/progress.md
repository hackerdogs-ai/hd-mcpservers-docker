# SpiderFoot MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`spiderfoot-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping sf.py CLI
  - [x] `run_spiderfoot` tool — run sf.py with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Add sf.py install steps to `Dockerfile` (cloned from [smicallef/spiderfoot](https://github.com/smicallef/spiderfoot), wrapper script, cryptography fix)
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8257
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8257** — SpiderFoot MCP Server (streamable-http)

## Notes

- Source: https://github.com/smicallef/spiderfoot
- Binary: `spiderfoot` (wrapper around `/opt/spiderfoot/sf.py`)
- SpiderFoot 4.0.0 with 231 OSINT modules
- SpiderFoot's `cryptography<4` pin conflicts with FastMCP; resolved by re-upgrading after install
- No API keys required for basic scans (some modules need keys for external services)
