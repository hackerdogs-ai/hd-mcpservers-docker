<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Calculator MCP Server

A Model Context Protocol server for calculating. This server enables LLMs to use calculator for precise numerical calculations.  Available T

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-calculator-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-calculator-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8407 \
  -p 8407:8407 \
  hackerdogs/acuvity-mcp-server-calculator-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-calculator-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-calculator-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8407` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-calculator-mcp:latest .
```

## Test

```bash
./test.sh
```
