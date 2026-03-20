<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# DuckDuckGo MCP server

A Model Context Protocol (MCP) server that provides web search capabilities through DuckDuckGo

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/duckduckgo-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name duckduckgo-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8413 \
  -p 8413:8413 \
  hackerdogs/duckduckgo-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "duckduckgo-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/duckduckgo-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8413` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/duckduckgo-mcp:latest .
```

## Test

```bash
./test.sh
```
