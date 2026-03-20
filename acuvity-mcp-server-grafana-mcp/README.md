<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Grafana MCP Server

The Grafana MCP Server MCP Server provides access to your Grafana instance and the surrounding ecosystem.

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-grafana-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-grafana-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8425 \
  -p 8425:8425 \
  hackerdogs/acuvity-mcp-server-grafana-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-grafana-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-grafana-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8425` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-grafana-mcp:latest .
```

## Test

```bash
./test.sh
```
