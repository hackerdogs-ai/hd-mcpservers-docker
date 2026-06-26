<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# USGS MCP

A comprehensive Model Context Protocol (MCP) server that integrates data from IRIS

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/earthquake-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name earthquake-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8457 \
  -p 8457:8457 \
  hackerdogs/earthquake-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "earthquake-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/earthquake-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8457` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/earthquake-mcp:latest .
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
    "earthquake-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/earthquake-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8457:8457 -e MCP_TRANSPORT=streamable-http hackerdogs/earthquake-mcp:latest
```

```json
{
  "mcpServers": {
    "earthquake-mcp": {
      "url": "http://localhost:8457/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
