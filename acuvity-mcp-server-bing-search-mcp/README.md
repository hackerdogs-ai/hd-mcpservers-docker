<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Bing Search MCP server

A Model Context Protocol (MCP) server for Microsoft Bing Search API integration

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-bing-search-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-bing-search-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8405 \
  -p 8405:8405 \
  hackerdogs/acuvity-mcp-server-bing-search-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-bing-search-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-bing-search-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8405` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-bing-search-mcp:latest .
```

## Test

```bash
./test.sh
```
