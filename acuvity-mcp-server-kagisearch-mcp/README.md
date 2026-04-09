<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Kagi Search MCP Server

MCP server for search queries and video summarization using Kagi

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-kagisearch-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-kagisearch-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8428 \
  -p 8428:8428 \
  hackerdogs/acuvity-mcp-server-kagisearch-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-kagisearch-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-kagisearch-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8428` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-kagisearch-mcp:latest .
```

## Test

```bash
./test.sh
```
