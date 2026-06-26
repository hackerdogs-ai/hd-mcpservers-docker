# whoisxmlapi-mcp

> WhoisXML API — remote streamable-HTTP endpoint (no local build needed).

## Description

Domain WHOIS lookups, historical data, DNS analysis, and monitoring.

## Category

Commercial

## Connection

This is a **remote-only** MCP server. No Docker image or local build is required.

| Transport | URL |
|-----------|-----|
| Streamable HTTP | `https://mcp.whoisxmlapi.com/mcp` |

## Setup

1. Sign up at [WhoisXML API](https://whoisxmlapi.com) and obtain your `WHOISXMLAPI_KEY`.
2. Add the `mcpServer.json` config to your MCP client.

## License

Proprietary — see [WhoisXML API](https://whoisxmlapi.com) for terms.

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "whoisxmlapi-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/whoisxmlapi-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8511:8511 -e MCP_TRANSPORT=streamable-http hackerdogs/whoisxmlapi-mcp:latest
```

```json
{
  "mcpServers": {
    "whoisxmlapi-mcp": {
      "url": "http://localhost:8511/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
