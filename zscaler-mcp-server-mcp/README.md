<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Zscaler MCP Server

The Zscaler MCP Server brings comprehensive Zscaler management capabilities directly to your AI agents and automation workflows. This compre

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/zscaler-mcp-server-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name zscaler-mcp-server-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8463 \
  -p 8463:8463 \
  hackerdogs/zscaler-mcp-server-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "zscaler-mcp-server-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/zscaler-mcp-server-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8463` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/zscaler-mcp-server-mcp:latest .
```

## Test

```bash
./test.sh
```
