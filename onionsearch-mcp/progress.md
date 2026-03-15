# OnionSearch MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`onionsearch-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping onionsearch CLI
  - [x] `run_onionsearch` tool — run onionsearch with arguments
  - [x] `onionsearch_search` tool — structured Dark Web search with parsed results
  - [x] Support stdio and streamable-http transports
  - [x] Automatic TOR_PROXY injection via --proxy flag
  - [x] Robust error handling and timeouts
  - [x] Concurrency-safe temp file handling (unique per invocation)
- [x] Create `Dockerfile` with onionsearch pip installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8372
- [x] Create `docker-compose.tor.yml` — separate Tor SOCKS5 proxy
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation (18/18 sections)
- [x] Create `progress.md` — this file
- [x] Make scripts executable
- [x] Build and test Docker image (6/6 tests pass)
- [x] Deep HTTP streamable test (init → notify → tools/list → tools/call) — all pass
- [x] Add to main README tool registry (Phase 4, #190)
- [x] Update SQL insert to mcp_server type

## Port Assignment

- **8372** — OnionSearch MCP Server (streamable-http)

## Notes

- Source: https://github.com/megadose/OnionSearch
- Binary: `onionsearch` (pip install onionsearch)
- Requires Tor SOCKS5 proxy running (default: 127.0.0.1:9050)
- Separate `docker-compose.tor.yml` provides a standalone Tor proxy container
- Supported engines: ahmia, darksearchio, onionland, notevil, darksearchenginer, phobos, onionsearchserver, torgle, torgle1, onionsearchengine, tordex, tor66, tormax, haystack, multivac, evosearch, deeplink
