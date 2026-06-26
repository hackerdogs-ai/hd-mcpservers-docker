# tavily-remote-mcp

> Tavily — remote streamable-HTTP endpoint (no local build needed).

## Description

Lightweight, production-ready server for live web search, crawling, and structured data extraction.

## Category

Commercial

## Connection

This is a **remote-only** MCP server. No Docker image or local build is required.

| Transport | URL |
|-----------|-----|
| Streamable HTTP | `https://mcp.tavily.com/mcp` |

## Setup

1. Sign up at [Tavily](https://tavily.com) and obtain your `TAVILY_API_KEY`.
2. Add the `mcpServer.json` config to your MCP client.

## License

Proprietary — see [Tavily](https://tavily.com) for terms.

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "tavily-remote-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/tavily-remote-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8513:8513 -e MCP_TRANSPORT=streamable-http hackerdogs/tavily-remote-mcp:latest
```

```json
{
  "mcpServers": {
    "tavily-remote-mcp": {
      "url": "http://localhost:8513/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
