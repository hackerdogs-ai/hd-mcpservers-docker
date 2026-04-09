<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Cortex MCP server

A security orchestration server that provides a unified interface for multiple threat intelligence analyzers. It allows AI agents to submit 

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/cortex-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name cortex-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8410 \
  -p 8410:8410 \
  hackerdogs/cortex-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "cortex-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/cortex-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8410` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/cortex-mcp:latest .
```

## Test

```bash
./test.sh
```
