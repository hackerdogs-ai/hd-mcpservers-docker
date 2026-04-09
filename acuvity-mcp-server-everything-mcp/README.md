<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# MCP Server Everything

MCP server that exercises all the features of the MCP protocol

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-everything-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-everything-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8431 \
  -p 8431:8431 \
  hackerdogs/acuvity-mcp-server-everything-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-everything-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-everything-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8431` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-everything-mcp:latest .
```

## Test

```bash
./test.sh
```
