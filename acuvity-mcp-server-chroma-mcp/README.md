<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Chroma MCP Server

This server provides data retrieval capabilities powered by Chroma vector database

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-chroma-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-chroma-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8408 \
  -p 8408:8408 \
  hackerdogs/acuvity-mcp-server-chroma-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-chroma-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-chroma-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8408` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-chroma-mcp:latest .
```

## Test

```bash
./test.sh
```
