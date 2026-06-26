<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# RSS MCP Server

This is a Model Context Protocol (MCP) server built with TypeScript. It provides a versatile tool to fetch and parse any standard RSS/Atom f

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/rss-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name rss-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8448 \
  -p 8448:8448 \
  hackerdogs/rss-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "rss-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/rss-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8448` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/rss-mcp:latest .
```

## Test

```bash
./test.sh
```

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "rss-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/rss-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8448:8448 -e MCP_TRANSPORT=streamable-http hackerdogs/rss-mcp:latest
```

```json
{
  "mcpServers": {
    "rss-mcp": {
      "url": "http://localhost:8448/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
