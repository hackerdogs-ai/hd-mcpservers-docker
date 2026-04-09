<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# World Bank MCP

A Model Context Protocol (MCP) server that enables interaction with the open World Bank data API. It allows AI assistants to access global e

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/world-bank-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name world-bank-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8459 \
  -p 8459:8459 \
  hackerdogs/world-bank-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "world-bank-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/world-bank-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8459` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/world-bank-mcp:latest .
```

## Test

```bash
./test.sh
```
