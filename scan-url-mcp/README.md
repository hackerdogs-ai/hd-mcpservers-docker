<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Scan URL MCP server

An enhanced security reconnaissance server that integrates with the urlscan.io API. It enables AI assistants to perform deep web analysis an

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/scan-url-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name scan-url-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8449 \
  -p 8449:8449 \
  hackerdogs/scan-url-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "scan-url-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/scan-url-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8449` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/scan-url-mcp:latest .
```

## Test

```bash
./test.sh
```
