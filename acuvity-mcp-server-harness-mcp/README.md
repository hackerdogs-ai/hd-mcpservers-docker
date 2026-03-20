<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Harness MCP Server

The Harness MCP Server is a Model Context Protocol (MCP) server that provides seamless integration with Harness APIs

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-harness-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-harness-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8426 \
  -p 8426:8426 \
  hackerdogs/acuvity-mcp-server-harness-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-harness-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-harness-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8426` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-harness-mcp:latest .
```

## Test

```bash
./test.sh
```
