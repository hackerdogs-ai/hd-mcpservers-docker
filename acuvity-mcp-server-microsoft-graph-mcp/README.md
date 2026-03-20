<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Microsoft Graph MCP Server

Connect to microsoft graph API to get applications

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-microsoft-graph-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-microsoft-graph-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8433 \
  -p 8433:8433 \
  hackerdogs/acuvity-mcp-server-microsoft-graph-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-microsoft-graph-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-microsoft-graph-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8433` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-microsoft-graph-mcp:latest .
```

## Test

```bash
./test.sh
```
