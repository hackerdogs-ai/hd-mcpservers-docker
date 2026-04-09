<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Marine Traffic MCP

A Model Context Protocol (MCP) server that connects AI assistants to the MarineTraffic API. It provides real-time vessel tracking

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/marinetraffic-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name marinetraffic-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8430 \
  -p 8430:8430 \
  hackerdogs/marinetraffic-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "marinetraffic-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/marinetraffic-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8430` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/marinetraffic-mcp:latest .
```

## Test

```bash
./test.sh
```
