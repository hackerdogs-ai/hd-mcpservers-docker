<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Hyperbrowser MCP Server

This is Hyperbrowser's Model Context Protocol (MCP) Server. It provides various tools to scrape

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-hyperbrowser-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-hyperbrowser-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8427 \
  -p 8427:8427 \
  hackerdogs/acuvity-mcp-server-hyperbrowser-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-hyperbrowser-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-hyperbrowser-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8427` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-hyperbrowser-mcp:latest .
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
    "acuvity-mcp-server-hyperbrowser-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-hyperbrowser-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8427:8427 -e MCP_TRANSPORT=streamable-http hackerdogs/acuvity-mcp-server-hyperbrowser-mcp:latest
```

```json
{
  "mcpServers": {
    "acuvity-mcp-server-hyperbrowser-mcp": {
      "url": "http://localhost:8427/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
