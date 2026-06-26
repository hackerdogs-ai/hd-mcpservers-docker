<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# PubMed MCP

A Model Context Protocol (MCP) server that enables AI assistants to search and analyze PubMed medical literature with advanced filtering

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/pubmed-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name pubmed-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8446 \
  -p 8446:8446 \
  hackerdogs/pubmed-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "pubmed-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/pubmed-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8446` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/pubmed-mcp:latest .
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
    "pubmed-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/pubmed-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8446:8446 -e MCP_TRANSPORT=streamable-http hackerdogs/pubmed-mcp:latest
```

```json
{
  "mcpServers": {
    "pubmed-mcp": {
      "url": "http://localhost:8446/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
