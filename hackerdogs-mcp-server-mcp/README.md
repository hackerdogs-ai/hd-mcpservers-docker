# hackerdogs-mcp-server-mcp

> Hackerdogs MCP — remote streamable-HTTP endpoint (no local build needed).

## Description

Transforms public, open, and adversarial signals into validated intelligence about emerging risks.

## Category

Commercial

## Connection

This is a **remote-only** MCP server. No Docker image or local build is required.

| Transport | URL |
|-----------|-----|
| Streamable HTTP | `https://mcp.hackerdogs.ai/mcp` |

## Setup

1. Sign up at [Hackerdogs](https://hackerdogs.ai) and obtain access.
2. Add the `mcpServer.json` config to your MCP client.


## Securely Accessing MCP

When running through the [Hackerdogs MCP Farm](https://hackerdogs.ai), servers are accessed through the authenticated gateway instead of direct container ports:

```json
{
  "mcpServers": {
    "hackerdogs-mcp-server-mcp": {
      "url": "http://localhost:8485/hackerdogs-mcp-server-mcp/mcp",
      "headers": {
        "Authorization": "Bearer <your-api-key>"
      }
    }
  }
}
```

> **Farm access:** The MCP Farm gateway handles authentication, rate limiting, and routing. Replace `localhost:8485` with your farm's host address and use your API key from the farm admin panel. See [Hackerdogs](https://hackerdogs.ai) for details.

## License

Proprietary — see [Hackerdogs](https://hackerdogs.ai) for terms.
