<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Mapbox MCP Server

The Mapbox MCP Server transforms any AI agent or application into a geospatially-aware system by providing seamless access to Mapbox's compr

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/mapboxserver-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name mapboxserver-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8429 \
  -p 8429:8429 \
  hackerdogs/mapboxserver-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "mapboxserver-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/mapboxserver-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8429` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/mapboxserver-mcp:latest .
```

## Test

```bash
./test.sh
```
