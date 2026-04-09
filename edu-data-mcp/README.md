<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# EduData Mcp Server

Overview edu-data-mcp-server is a Model Context Protocol (MCP) server that provides access to the Urban Institute's Education Data API. It e

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/edu-data-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name edu-data-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8416 \
  -p 8416:8416 \
  hackerdogs/edu-data-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "edu-data-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/edu-data-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8416` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/edu-data-mcp:latest .
```

## Test

```bash
./test.sh
```
