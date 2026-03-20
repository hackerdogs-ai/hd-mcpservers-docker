<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Minio AIStor MCP Server (Official)

The official Model Context Protocol server for MinIO’s exabyte-scale object storage. It provides AI agents with a natural language interface

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/aistor-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name aistor-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8434 \
  -p 8434:8434 \
  hackerdogs/aistor-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "aistor-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/aistor-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8434` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/aistor-mcp:latest .
```

## Test

```bash
./test.sh
```
