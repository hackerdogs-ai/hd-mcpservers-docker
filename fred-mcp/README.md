<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# FRED MCP SERVER

A Model Context Protocol (MCP) server providing structured access to over 800

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/fred-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name fred-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8423 \
  -p 8423:8423 \
  hackerdogs/fred-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "fred-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/fred-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8423` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/fred-mcp:latest .
```

## Test

```bash
./test.sh
```
