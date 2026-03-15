# DNSDumpster MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`dnsdumpster-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping dnsdumpster CLI
  - [x] `dnsdumpster_search` tool — structured passive DNS reconnaissance
  - [x] `run_dnsdumpster` tool — generic CLI passthrough
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing with normalized ASN/subdomain data
- [x] Add dnsdumpster install steps to `Dockerfile` (cloned from [nmmapper/dnsdumpster](https://github.com/nmmapper/dnsdumpster), wrapper script)
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8216
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable
- [x] Build and test Docker image (6/6 tests pass)

## Port Assignment

- **8216** — DNSDumpster MCP Server (streamable-http)

## Notes

- Source: https://github.com/nmmapper/dnsdumpster
- Binary: `dnsdumpster` (wrapper around `/opt/dnsdumpster/dnsdumpster.py`)
- Engines: DNSDumpster.com, Netcraft, VirusTotal, CRT.sh (SSL Certificate Transparency)
- Dependencies: requests, dnspython, simplejson, ip2geotools, ipwhois, wafw00f, graphviz
- Passive reconnaissance only — no direct queries to target
- Processing time: 30-120 seconds depending on domain size
- No API keys required
