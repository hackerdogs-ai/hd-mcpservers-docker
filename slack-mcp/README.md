<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Slack MCP Server

A specialized communication server for Slack that operates in a ""Stealth Mode

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/slack-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name slack-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8454 \
  -p 8454:8454 \
  hackerdogs/slack-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "slack-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/slack-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8454` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/slack-mcp:latest .
```

## Test

```bash
./test.sh
```

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "slack-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/slack-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8454:8454 -e MCP_TRANSPORT=streamable-http hackerdogs/slack-mcp:latest
```

```json
{
  "mcpServers": {
    "slack-mcp": {
      "url": "http://localhost:8454/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
