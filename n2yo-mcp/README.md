<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# N2YO MCP

A Model Context Protocol (MCP) server that connects AI assistants to the N2YO.com API for real-time satellite tracking. It enables users to 

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/n2yo-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name n2yo-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8435 \
  -p 8435:8435 \
  hackerdogs/n2yo-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "n2yo-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/n2yo-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8435` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/n2yo-mcp:latest .
```

## Test

```bash
./test.sh
```
