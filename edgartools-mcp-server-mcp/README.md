<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Edgar Tools MCP Server

EdgarTools supports all SEC form types including 10-K annual reports

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/edgartools-mcp-server-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name edgartools-mcp-server-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8415 \
  -p 8415:8415 \
  hackerdogs/edgartools-mcp-server-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "edgartools-mcp-server-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/edgartools-mcp-server-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8415` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/edgartools-mcp-server-mcp:latest .
```

## Test

```bash
./test.sh
```
