<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Slack MCP Server

MCP server for interacting with Slack

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-slack-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-slack-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8455 \
  -p 8455:8455 \
  hackerdogs/acuvity-mcp-server-slack-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-slack-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-slack-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8455` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-slack-mcp:latest .
```

## Test

```bash
./test.sh
```
