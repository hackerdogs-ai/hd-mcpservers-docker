# serpapi-mcp

> SerpApi — remote streamable-HTTP endpoint (no local build needed).

## Description

Integrates with SerpApi for comprehensive search engine results and data extraction. Google, Bing, YouTube, and more.

## Category

OSS

## Connection

This is a **remote-only** MCP server. No Docker image or local build is required.

| Transport | URL |
|-----------|-----|
| Streamable HTTP | `https://mcp.serpapi.com/mcp` |

## Setup

1. Sign up at [SerpApi](https://serpapi.com) and obtain your `SERPAPI_API_KEY`.
2. Add the `mcpServer.json` config to your MCP client.

## License

Proprietary — see [SerpApi](https://serpapi.com) for terms.

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "serpapi-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/serpapi-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8514:8514 -e MCP_TRANSPORT=streamable-http hackerdogs/serpapi-mcp:latest
```

```json
{
  "mcpServers": {
    "serpapi-mcp": {
      "url": "http://localhost:8514/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
