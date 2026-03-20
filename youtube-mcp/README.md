<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# YouTube MCP Server

A Model Context Protocol (MCP) server implementation for YouTube

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/youtube-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name youtube-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8462 \
  -p 8462:8462 \
  hackerdogs/youtube-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "youtube-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/youtube-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8462` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/youtube-mcp:latest .
```

## Test

```bash
./test.sh
```
