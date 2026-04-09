<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Alpha Vantage MCP

A Model Context Protocol (MCP) server providing real-time and historical financial data. It offers a standardized interface for stock quotes

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/alphavantage-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name alphavantage-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8402 \
  -p 8402:8402 \
  hackerdogs/alphavantage-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "alphavantage-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/alphavantage-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8402` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/alphavantage-mcp:latest .
```

## Test

```bash
./test.sh
```
