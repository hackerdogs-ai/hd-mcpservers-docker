<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Microsoft Azure MCP Server

Integrates AI agents with Azure services for enhanced functionality.

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-azure-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-azure-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8432 \
  -p 8432:8432 \
  hackerdogs/acuvity-mcp-server-azure-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-azure-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-azure-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8432` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-azure-mcp:latest .
```

## Test

```bash
./test.sh
```
