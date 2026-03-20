<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Docker MCP server

An MCP server for managing Docker with natural language!  What can it do? Compose containers with natural language Introspect & debug runnin

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-docker-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-docker-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8412 \
  -p 8412:8412 \
  hackerdogs/acuvity-mcp-server-docker-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-docker-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-docker-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8412` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-docker-mcp:latest .
```

## Test

```bash
./test.sh
```
