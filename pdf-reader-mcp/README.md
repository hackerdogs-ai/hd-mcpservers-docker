<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# PDF Reader MCP Server (Sylphx)

MCP server for reading and extracting text from PDF files via URLs. Uses @sylphx/pdf-reader-mcp npm package. Supports PDF URLs via sources a

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/pdf-reader-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name pdf-reader-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8442 \
  -p 8442:8442 \
  hackerdogs/pdf-reader-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "pdf-reader-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/pdf-reader-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8442` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/pdf-reader-mcp:latest .
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
    "pdf-reader-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/pdf-reader-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8442:8442 -e MCP_TRANSPORT=streamable-http hackerdogs/pdf-reader-mcp:latest
```

```json
{
  "mcpServers": {
    "pdf-reader-mcp": {
      "url": "http://localhost:8442/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
