<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Everything Wrong MCP Server

A demonstration Model Context Protocol (MCP) server that exposes a variety of “tools”—some benign

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-everything-wrong-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-everything-wrong-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8418 \
  -p 8418:8418 \
  hackerdogs/acuvity-mcp-server-everything-wrong-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-everything-wrong-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-everything-wrong-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8418` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-everything-wrong-mcp:latest .
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
    "acuvity-mcp-server-everything-wrong-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-everything-wrong-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8418:8418 -e MCP_TRANSPORT=streamable-http hackerdogs/acuvity-mcp-server-everything-wrong-mcp:latest
```

```json
{
  "mcpServers": {
    "acuvity-mcp-server-everything-wrong-mcp": {
      "url": "http://localhost:8418/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
