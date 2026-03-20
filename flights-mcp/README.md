<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Flights MCP

A Model Context Protocol (MCP) server that provides flight search capabilities by integrating with the Aviasales Flight Search API. It allow

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/flights-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name flights-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8422 \
  -p 8422:8422 \
  hackerdogs/flights-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "flights-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/flights-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8422` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/flights-mcp:latest .
```

## Test

```bash
./test.sh
```
