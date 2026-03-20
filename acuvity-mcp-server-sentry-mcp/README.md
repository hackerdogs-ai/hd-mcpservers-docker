<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Sentry MCP Server

Retrieving and analyzing application issues from Sentry.io.

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-sentry-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-sentry-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8452 \
  -p 8452:8452 \
  hackerdogs/acuvity-mcp-server-sentry-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-sentry-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-sentry-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8452` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-sentry-mcp:latest .
```

## Test

```bash
./test.sh
```
