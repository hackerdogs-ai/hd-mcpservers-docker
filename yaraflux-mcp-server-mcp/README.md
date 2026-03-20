<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# YaraFlux MCP server

A YARA-based Model Context Protocol (MCP) server that integrates with AI assistants to perform automated malware scanning and threat analysi

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/yaraflux-mcp-server-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name yaraflux-mcp-server-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8461 \
  -p 8461:8461 \
  hackerdogs/yaraflux-mcp-server-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "yaraflux-mcp-server-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/yaraflux-mcp-server-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8461` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/yaraflux-mcp-server-mcp:latest .
```

## Test

```bash
./test.sh
```
