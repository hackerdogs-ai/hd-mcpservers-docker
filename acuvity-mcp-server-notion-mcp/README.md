<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Notion MCP Server

Notion MCP is our hosted server that gives AI tools secure access to your Notion workspace.  Generate documentation — Generate PRDs

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-notion-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-notion-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8437 \
  -p 8437:8437 \
  hackerdogs/acuvity-mcp-server-notion-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-notion-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-notion-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8437` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-notion-mcp:latest .
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
    "acuvity-mcp-server-notion-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-notion-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8437:8437 -e MCP_TRANSPORT=streamable-http hackerdogs/acuvity-mcp-server-notion-mcp:latest
```

```json
{
  "mcpServers": {
    "acuvity-mcp-server-notion-mcp": {
      "url": "http://localhost:8437/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
