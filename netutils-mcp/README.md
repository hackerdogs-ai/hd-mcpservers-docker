<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# NetUtils

A comprehensive network and domain analysis toolkit for AI assistants. It provides a suite of tools for DNS exploration (A

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/netutils-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name netutils-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8436 \
  -p 8436:8436 \
  hackerdogs/netutils-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "netutils-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/netutils-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8436` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/netutils-mcp:latest .
```

## Test

```bash
./test.sh
```
