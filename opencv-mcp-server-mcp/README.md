<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# OpenCV MCP Server

OpenCV MCP Server is a Python package that provides OpenCV's image and video processing capabilities through the Model Context Protocol (MCP

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/opencv-mcp-server-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name opencv-mcp-server-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8440 \
  -p 8440:8440 \
  hackerdogs/opencv-mcp-server-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "opencv-mcp-server-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/opencv-mcp-server-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8440` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/opencv-mcp-server-mcp:latest .
```

## Test

```bash
./test.sh
```
