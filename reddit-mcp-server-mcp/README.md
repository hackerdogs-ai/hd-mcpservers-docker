<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Reddit MCP Server

A comprehensive Model Context Protocol (MCP) server for Reddit integration. This server enables AI agents to interact with Reddit programmat

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/reddit-mcp-server-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name reddit-mcp-server-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8447 \
  -p 8447:8447 \
  hackerdogs/reddit-mcp-server-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "reddit-mcp-server-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/reddit-mcp-server-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8447` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/reddit-mcp-server-mcp:latest .
```

## Test

```bash
./test.sh
```
