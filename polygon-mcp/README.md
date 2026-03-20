<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Polygon MCP server

Polygon MCP Server A Model Context Protocol (MCP) server that provides tools for interacting with the Polygon.io API for market data. A fina

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/polygon-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name polygon-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8445 \
  -p 8445:8445 \
  hackerdogs/polygon-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "polygon-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/polygon-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8445` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/polygon-mcp:latest .
```

## Test

```bash
./test.sh
```
