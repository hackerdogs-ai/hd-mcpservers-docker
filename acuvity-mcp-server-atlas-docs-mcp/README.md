<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Atlas Docs MCP Server

Atlas Docs MCP server:  Provides technical documentation for libraries and frameworks Processes the official docs into a clean markdown vers

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-atlas-docs-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-atlas-docs-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8403 \
  -p 8403:8403 \
  hackerdogs/acuvity-mcp-server-atlas-docs-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-atlas-docs-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-atlas-docs-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8403` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-atlas-docs-mcp:latest .
```

## Test

```bash
./test.sh
```
