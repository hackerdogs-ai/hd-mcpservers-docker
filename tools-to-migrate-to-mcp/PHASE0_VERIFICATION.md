# Phase 0 Verification — ALREADY_BUILT (13 servers)

**Completed:** All 13 servers verified against §2 (Project requirements).

## Verification summary

| # | mcp_server_name | Present | streamable-http | README entry | Port |
|---|-----------------|---------|-----------------|--------------|------|
| 1 | dnsdumpster-mcp | ✅ | ✅ | ✅ | 8216 |
| 2 | holehe-mcp | ✅ | ✅ | ✅ | 8219 |
| 3 | julius-mcp | ✅ | ✅ | ✅ | 8100 |
| 4 | maigret-mcp | ✅ | ✅ | ✅ | 8221 |
| 5 | misp-mcp | ✅ | ✅ | ✅ | 8371 |
| 6 | onionsearch-mcp | ✅ | ✅ | ✅ | 8372 |
| 7 | opencti-mcp | ✅ | ✅ | ✅ | 8370 |
| 8 | otx-mcp | ✅ | ✅ | ✅ | 8368 |
| 9 | semgrep-mcp | ✅ | ✅ | ✅ | 8335 |
| 10 | sherlock-mcp | ✅ | ✅ | ✅ | 8317 |
| 11 | subfinder-mcp | ✅ | ✅ | ⚠️→✅ | 8367 |
| 12 | virustotal-mcp | ✅ | ✅ | ✅ | 8369 |
| 13 | zmap-mcp | ✅ | ✅ | ✅ | 8303 |

**Fix applied:** subfinder-mcp was missing from the root README tool table; added to Phase 4 table with port 8367.

## Checklist per server

- **Directory** `/<mcp_server_name>/` exists with Dockerfile, mcp_server.py, README.md, mcpServer.json, docker-compose.yml, test.sh, requirements.txt.
- **mcp_server.py** uses `MCP_TRANSPORT` and `MCP_PORT`; when `streamable-http`, runs `mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)`.
- **Root README** lists the tool and port in the registry table.

Phase 0 is complete.
