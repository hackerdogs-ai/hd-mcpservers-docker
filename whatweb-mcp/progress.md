# WhatWeb MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`whatweb-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping whatweb CLI
  - [x] `run_whatweb` tool — run whatweb with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add whatweb install steps to `Dockerfile` (see [urbanadventurer/WhatWeb](https://github.com/urbanadventurer/WhatWeb))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8281
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8281** — WhatWeb MCP Server (streamable-http)

## Notes

- Source: https://github.com/urbanadventurer/WhatWeb
- Binary: `whatweb`
- Install: see https://github.com/urbanadventurer/WhatWeb for installation instructions
