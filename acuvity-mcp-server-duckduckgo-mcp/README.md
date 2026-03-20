<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# DuckDuckGo Search MCP Server (Acuvity)

A Model Context Protocol (MCP) server that provides web search capabilities through DuckDuckGo

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-duckduckgo-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-duckduckgo-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8414 \
  -p 8414:8414 \
  hackerdogs/acuvity-mcp-server-duckduckgo-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-duckduckgo-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-duckduckgo-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8414` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-duckduckgo-mcp:latest .
```

## Test

```bash
./test.sh
```
