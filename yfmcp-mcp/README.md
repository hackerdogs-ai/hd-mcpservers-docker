<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Yahoo Finance MCP SERVER

Yahoo Finance MCP Server A simple MCP server for Yahoo Finance using yfinance. This server provides a set of tools to fetch stock data

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/yfmcp-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name yfmcp-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8460 \
  -p 8460:8460 \
  hackerdogs/yfmcp-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "yfmcp-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/yfmcp-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8460` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/yfmcp-mcp:latest .
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
    "yfmcp-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/yfmcp-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8460:8460 -e MCP_TRANSPORT=streamable-http hackerdogs/yfmcp-mcp:latest
```

```json
{
  "mcpServers": {
    "yfmcp-mcp": {
      "url": "http://localhost:8460/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
