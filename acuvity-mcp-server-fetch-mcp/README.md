<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Fetch Mcp Server

Fetch MCP Server A Model Context Protocol server that provides web content fetching capabilities. This server enables LLMs to retrieve and p

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-fetch-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-fetch-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8419 \
  -p 8419:8419 \
  hackerdogs/acuvity-mcp-server-fetch-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-fetch-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-fetch-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8419` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-fetch-mcp:latest .
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
    "acuvity-mcp-server-fetch-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-fetch-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8419:8419 -e MCP_TRANSPORT=streamable-http hackerdogs/acuvity-mcp-server-fetch-mcp:latest
```

```json
{
  "mcpServers": {
    "acuvity-mcp-server-fetch-mcp": {
      "url": "http://localhost:8419/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
