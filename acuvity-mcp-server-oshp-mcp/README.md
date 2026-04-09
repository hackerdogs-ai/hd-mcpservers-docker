<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# OSHP MCP Server

Analyzes HTTP response headers against OWASP security standards with recommendations  The OWASP Secure Headers Project (OSHP) provides infor

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-oshp-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-oshp-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8441 \
  -p 8441:8441 \
  hackerdogs/acuvity-mcp-server-oshp-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-oshp-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-oshp-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8441` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-oshp-mcp:latest .
```

## Test

```bash
./test.sh
```
