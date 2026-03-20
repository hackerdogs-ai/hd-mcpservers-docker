<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Financial Datasets MCP

A comprehensive financial data server that connects AI assistants to real-time and historical stock market intelligence. It provides specifi

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/financial-datasets-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name financial-datasets-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8420 \
  -p 8420:8420 \
  hackerdogs/financial-datasets-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "financial-datasets-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/financial-datasets-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8420` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/financial-datasets-mcp:latest .
```

## Test

```bash
./test.sh
```
