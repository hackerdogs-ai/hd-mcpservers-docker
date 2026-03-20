<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# SEC Edgar MCP Server

MCP server for accessing SEC EDGAR filings. Connects AI assistants to company filings

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/sec-edgar-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name sec-edgar-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8451 \
  -p 8451:8451 \
  hackerdogs/sec-edgar-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "sec-edgar-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/sec-edgar-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8451` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/sec-edgar-mcp:latest .
```

## Test

```bash
./test.sh
```
