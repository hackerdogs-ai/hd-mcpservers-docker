# censys-platform-mcp

> Censys MCP Server — remote streamable-HTTP endpoint (no local build needed).

## Description

After configuring your integration, AI agents can query Censys for host, certificate, and service information. Example: "What services are running on 8.8.8.8?"

## Category

Commercial

## Connection

Production uses the **hosted** Censys Platform MCP URL (see `mcpServer.json`). This folder also includes a **local FastMCP Docker stub** so you can run `test.sh` (5-step compliance: image, stdio, HTTP).

| Transport | URL |
|-----------|-----|
| Streamable HTTP | `https://mcp.platform.censys.io/platform/mcp/` (with token + org headers) |

## Setup

1. Sign up at [censys.io](https://censys.io) and obtain credentials.
2. Add the `mcpServer.json` config to your MCP client.

## License

Proprietary — see [Censys](https://censys.io) for terms.
