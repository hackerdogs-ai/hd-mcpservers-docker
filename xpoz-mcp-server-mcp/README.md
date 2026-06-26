# xpoz-mcp-server-mcp

> XPoz — remote streamable-HTTP endpoint (no local build needed).

## Description

Social intelligence for AI agents. Search and analyze live social media through natural language. No API keys needed.

## Category

Commercial

## Connection

This is a **remote-only** MCP server. No Docker image or local build is required.

| Transport | URL |
|-----------|-----|
| Streamable HTTP | `https://mcp.xpoz.io/mcp` |

## Setup

1. Add the `mcpServer.json` config to your MCP client (no API key required).
2. Connect to the remote endpoint to start using social intelligence tools.

## License

Proprietary — see [XPoz](https://xpoz.io) for terms.

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "xpoz-mcp-server-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/xpoz-mcp-server-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8510:8510 -e MCP_TRANSPORT=streamable-http hackerdogs/xpoz-mcp-server-mcp:latest
```

```json
{
  "mcpServers": {
    "xpoz-mcp-server-mcp": {
      "url": "http://localhost:8510/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
