<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Code Runner MCP Server

MCP Server for running code snippet and show the result.  It supports running multiple programming languages: JavaScript

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/mcp-server-code-runner-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name mcp-server-code-runner-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8409 \
  -p 8409:8409 \
  hackerdogs/mcp-server-code-runner-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "mcp-server-code-runner-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/mcp-server-code-runner-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8409` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/mcp-server-code-runner-mcp:latest .
```

## Test

```bash
./test.sh
```
